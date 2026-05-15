"""
HIGH-FREQUENCY SCALPING STRATEGY
Target: 2.5% daily return (15 trades/day @ 72% win rate)

Strategy Logic:
- 1-5 minute timeframes
- Order book imbalance detection
- Tight entry/exit (0.25% profit, 0.15% stop loss)
- Sub-second execution required
- 20x leverage on 10% position size

Signal Generation:
1. Order book depth imbalance >60%
2. Volume spike >2x average
3. Momentum confirmation (price moving in direction)
4. Tight spread <0.05%
"""

import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from collections import deque
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ScalpSignal:
    """Scalp trading signal"""
    timestamp: datetime
    symbol: str
    side: str  # 'long' or 'short'
    entry_price: float
    confidence: float
    reason: str

    # Signal components
    orderbook_imbalance: float
    volume_spike_ratio: float
    momentum_score: float
    spread_pct: float


class HighFrequencyScalper:
    """
    Ultra-fast scalping strategy for 1-5m timeframes

    Target Performance:
    - 15 trades per day
    - 72% win rate
    - 0.25% avg profit per trade
    - 0.15% avg loss per trade
    - 2.5% daily return with 20x leverage
    """

    def __init__(self, symbol: str = "BTC/USDT"):
        self.symbol = symbol

        # Strategy parameters
        self.leverage = 20
        self.position_size_pct = 0.10  # 10% of capital

        # Entry/exit thresholds
        self.profit_target_pct = 0.0025  # 0.25%
        self.stop_loss_pct = 0.0015  # 0.15%

        # Signal thresholds
        self.min_orderbook_imbalance = 0.60  # 60% bid or ask dominance
        self.min_volume_spike = 2.0  # 2x normal volume
        self.min_momentum_score = 0.65
        self.max_spread_pct = 0.0005  # 0.05% max spread

        # Data buffers
        self.recent_trades = deque(maxlen=100)
        self.volume_history = deque(maxlen=20)
        self.price_history = deque(maxlen=50)

        # Performance tracking
        self.trades_today = 0
        self.max_trades_per_day = 20
        self.wins = 0
        self.losses = 0

    def calculate_orderbook_imbalance(self, bids: List[tuple], asks: List[tuple]) -> float:
        """
        Calculate order book depth imbalance

        Returns: -1.0 to +1.0
        - Positive = more bid volume (bullish)
        - Negative = more ask volume (bearish)
        """
        # Sum up top 10 levels
        total_bid_volume = sum(qty for price, qty in bids[:10])
        total_ask_volume = sum(qty for price, qty in asks[:10])

        total_volume = total_bid_volume + total_ask_volume
        if total_volume == 0:
            return 0.0

        imbalance = (total_bid_volume - total_ask_volume) / total_volume
        return imbalance

    def calculate_volume_spike(self, current_volume: float) -> float:
        """
        Calculate volume spike ratio

        Returns: current_volume / avg_volume
        """
        if len(self.volume_history) < 5:
            self.volume_history.append(current_volume)
            return 1.0

        avg_volume = np.mean(list(self.volume_history))
        self.volume_history.append(current_volume)

        if avg_volume == 0:
            return 1.0

        return current_volume / avg_volume

    def calculate_momentum_score(self, current_price: float) -> Tuple[float, str]:
        """
        Calculate price momentum score

        Returns: (score 0-1, direction 'up'/'down')
        """
        if len(self.price_history) < 10:
            self.price_history.append(current_price)
            return 0.5, 'neutral'

        prices = list(self.price_history)
        self.price_history.append(current_price)

        # Calculate short-term momentum (last 10 candles)
        sma_short = np.mean(prices[-10:])
        sma_long = np.mean(prices[-20:] if len(prices) >= 20 else prices)

        # Price position relative to SMAs
        if sma_long == 0:
            return 0.5, 'neutral'

        # Calculate momentum strength
        momentum_strength = abs((sma_short - sma_long) / sma_long)

        # Normalize to 0-1
        score = min(1.0, momentum_strength / 0.01)  # 1% move = max score

        # Determine direction
        if current_price > sma_short > sma_long:
            direction = 'up'
            score = min(1.0, score + 0.2)  # Bonus for aligned trend
        elif current_price < sma_short < sma_long:
            direction = 'down'
            score = min(1.0, score + 0.2)
        else:
            direction = 'neutral'
            score *= 0.7  # Penalty for mixed signals

        return score, direction

    def generate_signal(self,
                       orderbook: Dict,
                       current_price: float,
                       current_volume: float) -> Optional[ScalpSignal]:
        """
        Generate scalping signal based on order book + volume + momentum

        Returns: ScalpSignal or None
        """

        # Check if we've hit daily trade limit
        if self.trades_today >= self.max_trades_per_day:
            logger.debug("Daily trade limit reached")
            return None

        # Extract orderbook data
        bids = orderbook.get('bids', [])
        asks = orderbook.get('asks', [])

        if not bids or not asks:
            return None

        # Calculate spread
        best_bid = bids[0][0]
        best_ask = asks[0][0]
        spread = best_ask - best_bid
        mid_price = (best_bid + best_ask) / 2
        spread_pct = spread / mid_price

        # Filter 1: Spread must be tight
        if spread_pct > self.max_spread_pct:
            logger.debug(f"Spread too wide: {spread_pct*100:.4f}%")
            return None

        # Calculate signal components
        orderbook_imbalance = self.calculate_orderbook_imbalance(bids, asks)
        volume_spike_ratio = self.calculate_volume_spike(current_volume)
        momentum_score, momentum_direction = self.calculate_momentum_score(current_price)

        # Determine trade direction
        side = None
        confidence = 0.0
        reason_parts = []

        # LONG signal conditions
        if (orderbook_imbalance > self.min_orderbook_imbalance and
            volume_spike_ratio >= self.min_volume_spike and
            momentum_direction == 'up'):

            side = 'long'
            confidence = (
                (orderbook_imbalance + 1) / 2 * 0.4 +  # 40% weight
                min(1.0, volume_spike_ratio / 3) * 0.3 +  # 30% weight
                momentum_score * 0.3  # 30% weight
            )

            reason_parts.append(f"Orderbook: {orderbook_imbalance*100:.1f}% bid dominance")
            reason_parts.append(f"Volume: {volume_spike_ratio:.1f}x spike")
            reason_parts.append(f"Momentum: {momentum_score*100:.0f}% upward")

        # SHORT signal conditions
        elif (orderbook_imbalance < -self.min_orderbook_imbalance and
              volume_spike_ratio >= self.min_volume_spike and
              momentum_direction == 'down'):

            side = 'short'
            confidence = (
                (abs(orderbook_imbalance) + 1) / 2 * 0.4 +
                min(1.0, volume_spike_ratio / 3) * 0.3 +
                momentum_score * 0.3
            )

            reason_parts.append(f"Orderbook: {abs(orderbook_imbalance)*100:.1f}% ask dominance")
            reason_parts.append(f"Volume: {volume_spike_ratio:.1f}x spike")
            reason_parts.append(f"Momentum: {momentum_score*100:.0f}% downward")

        # No clear signal
        if side is None or confidence < 0.70:
            return None

        # Create signal
        signal = ScalpSignal(
            timestamp=datetime.now(),
            symbol=self.symbol,
            side=side,
            entry_price=current_price,
            confidence=confidence,
            reason=" | ".join(reason_parts),
            orderbook_imbalance=orderbook_imbalance,
            volume_spike_ratio=volume_spike_ratio,
            momentum_score=momentum_score,
            spread_pct=spread_pct
        )

        return signal

    def calculate_targets(self, entry_price: float, side: str) -> Dict[str, float]:
        """Calculate profit target and stop loss"""

        if side == 'long':
            take_profit = entry_price * (1 + self.profit_target_pct)
            stop_loss = entry_price * (1 - self.stop_loss_pct)
        else:  # short
            take_profit = entry_price * (1 - self.profit_target_pct)
            stop_loss = entry_price * (1 + self.stop_loss_pct)

        return {
            'take_profit': take_profit,
            'stop_loss': stop_loss,
            'profit_target_pct': self.profit_target_pct * 100,
            'stop_loss_pct': self.stop_loss_pct * 100
        }

    def should_exit(self, entry_price: float, current_price: float,
                   side: str, holding_time_seconds: float) -> Tuple[bool, str]:
        """
        Determine if position should be exited

        Returns: (should_exit: bool, reason: str)
        """

        # Calculate P&L
        if side == 'long':
            pnl_pct = (current_price - entry_price) / entry_price
        else:  # short
            pnl_pct = (entry_price - current_price) / entry_price

        # Take profit hit
        if pnl_pct >= self.profit_target_pct:
            return True, f"Take profit hit: {pnl_pct*100:.2f}%"

        # Stop loss hit
        if pnl_pct <= -self.stop_loss_pct:
            return True, f"Stop loss hit: {pnl_pct*100:.2f}%"

        # Time-based exit (max 5 minutes for scalp)
        max_holding_seconds = 300  # 5 minutes
        if holding_time_seconds >= max_holding_seconds:
            return True, f"Time exit: {holding_time_seconds:.0f}s ({pnl_pct*100:+.2f}%)"

        return False, ""

    def record_trade_result(self, is_win: bool):
        """Record trade result for tracking"""
        self.trades_today += 1

        if is_win:
            self.wins += 1
        else:
            self.losses += 1

    def get_win_rate(self) -> float:
        """Get current win rate"""
        total = self.wins + self.losses
        if total == 0:
            return 0.0
        return self.wins / total

    def reset_daily_stats(self):
        """Reset daily statistics"""
        self.trades_today = 0
        logger.info(f"Daily stats reset. Session total: W:{self.wins} L:{self.losses} WR:{self.get_win_rate()*100:.1f}%")

    def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'symbol': self.symbol,
            'trades_today': self.trades_today,
            'max_trades_per_day': self.max_trades_per_day,
            'total_wins': self.wins,
            'total_losses': self.losses,
            'win_rate': self.get_win_rate(),
            'target_daily_return': 2.5,
            'leverage': self.leverage,
            'position_size_pct': self.position_size_pct * 100
        }


# Test the strategy
if __name__ == '__main__':
    scalper = HighFrequencyScalper("BTC/USDT")

    print("=" * 80)
    print("🚀 HIGH-FREQUENCY SCALPING STRATEGY TEST")
    print("=" * 80)

    print("\n📊 Strategy Parameters:")
    status = scalper.get_status()
    for key, value in status.items():
        print(f"   {key}: {value}")

    print("\n🧪 Simulating 20 signals...")

    signals_generated = 0

    for i in range(100):
        # Simulate market data
        current_price = np.random.uniform(40000, 45000)
        current_volume = np.random.uniform(10, 100)

        # Simulate orderbook with random imbalance
        imbalance = np.random.uniform(-1, 1)
        if imbalance > 0:
            # More bids (bullish)
            bid_volume = 100
            ask_volume = 100 * (1 - abs(imbalance))
        else:
            # More asks (bearish)
            bid_volume = 100 * (1 - abs(imbalance))
            ask_volume = 100

        bids = [(current_price * 0.9999, bid_volume)] * 10
        asks = [(current_price * 1.0001, ask_volume)] * 10

        orderbook = {
            'bids': bids,
            'asks': asks
        }

        # Generate signal
        signal = scalper.generate_signal(orderbook, current_price, current_volume)

        if signal:
            signals_generated += 1
            print(f"\n✅ Signal #{signals_generated}:")
            print(f"   Side: {signal.side.upper()}")
            print(f"   Entry: ${signal.entry_price:,.2f}")
            print(f"   Confidence: {signal.confidence*100:.1f}%")
            print(f"   Reason: {signal.reason}")

            targets = scalper.calculate_targets(signal.entry_price, signal.side)
            print(f"   Take Profit: ${targets['take_profit']:,.2f} (+{targets['profit_target_pct']:.2f}%)")
            print(f"   Stop Loss: ${targets['stop_loss']:,.2f} (-{targets['stop_loss_pct']:.2f}%)")

            # Simulate trade result (72% win rate)
            is_win = np.random.random() < 0.72
            scalper.record_trade_result(is_win)

            if signals_generated >= 20:
                break

    print(f"\n" + "=" * 80)
    print("📈 SIMULATION RESULTS")
    print("=" * 80)
    print(f"Signals Generated: {signals_generated}")
    print(f"Win Rate: {scalper.get_win_rate()*100:.1f}% (Target: 72%)")
    print(f"Wins: {scalper.wins}")
    print(f"Losses: {scalper.losses}")
    print("=" * 80)
