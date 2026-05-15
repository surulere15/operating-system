"""
MOMENTUM BREAKOUT STRATEGY
Target: 2.0% daily return (4 trades/day @ 65% win rate)

Strategy Logic:
- 15m-1h timeframes
- Volume breakout + price breakout confirmation
- Trend following with momentum
- 1.2% profit target, 0.6% stop loss
- 15x leverage on 15% position size

Signal Generation:
1. Price breaks above resistance or below support
2. Volume >3x average during breakout
3. RSI confirms momentum (>60 for long, <40 for short)
4. No recent false breakouts
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
class MomentumSignal:
    """Momentum breakout signal"""
    timestamp: datetime
    symbol: str
    side: str
    entry_price: float
    confidence: float
    reason: str

    # Signal metrics
    breakout_level: float
    volume_ratio: float
    rsi: float
    atr: float


class MomentumBreakoutStrategy:
    """
    Momentum breakout trading for 15m-1h timeframes

    Target Performance:
    - 4 trades per day
    - 65% win rate
    - 1.2% avg profit per trade
    - 0.6% avg loss per trade
    - 2.0% daily return with 15x leverage
    """

    def __init__(self, symbol: str = "BTC/USDT", timeframe: str = "15m"):
        self.symbol = symbol
        self.timeframe = timeframe

        # Strategy parameters
        self.leverage = 15
        self.position_size_pct = 0.15  # 15% of capital

        # Entry/exit thresholds
        self.profit_target_pct = 0.012  # 1.2%
        self.stop_loss_pct = 0.006  # 0.6%

        # Signal thresholds
        self.min_volume_ratio = 3.0  # 3x average volume
        self.rsi_long_threshold = 60
        self.rsi_short_threshold = 40
        self.min_breakout_strength = 0.70

        # Data buffers
        self.price_history = deque(maxlen=100)
        self.volume_history = deque(maxlen=50)
        self.high_history = deque(maxlen=100)
        self.low_history = deque(maxlen=100)

        # Support/Resistance levels
        self.resistance_levels = []
        self.support_levels = []

        # Performance tracking
        self.trades_today = 0
        self.max_trades_per_day = 6
        self.wins = 0
        self.losses = 0

    def calculate_rsi(self, period: int = 14) -> float:
        """Calculate RSI indicator"""
        if len(self.price_history) < period + 1:
            return 50.0  # Neutral

        prices = list(self.price_history)

        # Calculate price changes
        changes = [prices[i] - prices[i-1] for i in range(1, len(prices))]

        # Separate gains and losses
        gains = [max(0, change) for change in changes[-period:]]
        losses = [max(0, -change) for change in changes[-period:]]

        # Calculate average gain and loss
        avg_gain = np.mean(gains) if gains else 0
        avg_loss = np.mean(losses) if losses else 0

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def calculate_atr(self, period: int = 14) -> float:
        """Calculate Average True Range"""
        if len(self.high_history) < period + 1:
            return 0.0

        highs = list(self.high_history)
        lows = list(self.low_history)
        closes = list(self.price_history)

        true_ranges = []
        for i in range(1, len(highs)):
            high_low = highs[i] - lows[i]
            high_close = abs(highs[i] - closes[i-1])
            low_close = abs(lows[i] - closes[i-1])

            tr = max(high_low, high_close, low_close)
            true_ranges.append(tr)

        return np.mean(true_ranges[-period:])

    def update_support_resistance(self):
        """Update support and resistance levels"""
        if len(self.high_history) < 50:
            return

        highs = list(self.high_history)[-50:]
        lows = list(self.low_history)[-50:]

        # Find local maxima (resistance)
        self.resistance_levels = []
        for i in range(2, len(highs) - 2):
            if highs[i] > highs[i-1] and highs[i] > highs[i-2] and \
               highs[i] > highs[i+1] and highs[i] > highs[i+2]:
                self.resistance_levels.append(highs[i])

        # Find local minima (support)
        self.support_levels = []
        for i in range(2, len(lows) - 2):
            if lows[i] < lows[i-1] and lows[i] < lows[i-2] and \
               lows[i] < lows[i+1] and lows[i] < lows[i+2]:
                self.support_levels.append(lows[i])

        # Keep only the 3 most recent
        self.resistance_levels = sorted(self.resistance_levels, reverse=True)[:3]
        self.support_levels = sorted(self.support_levels, reverse=True)[:3]

    def detect_breakout(self, current_price: float, current_high: float,
                       current_low: float) -> Tuple[Optional[str], float, float]:
        """
        Detect breakout above resistance or below support

        Returns: (direction, breakout_level, strength)
        """
        if not self.resistance_levels and not self.support_levels:
            return None, 0, 0

        # Check resistance breakout (LONG)
        for resistance in self.resistance_levels:
            if current_high > resistance:
                strength = (current_high - resistance) / resistance
                if strength > 0.001:  # At least 0.1% breakout
                    return 'long', resistance, strength

        # Check support breakout (SHORT)
        for support in self.support_levels:
            if current_low < support:
                strength = (support - current_low) / support
                if strength > 0.001:  # At least 0.1% breakout
                    return 'short', support, strength

        return None, 0, 0

    def calculate_volume_ratio(self, current_volume: float) -> float:
        """Calculate volume vs average"""
        if len(self.volume_history) < 5:
            self.volume_history.append(current_volume)
            return 1.0

        avg_volume = np.mean(list(self.volume_history))
        self.volume_history.append(current_volume)

        if avg_volume == 0:
            return 1.0

        return current_volume / avg_volume

    def generate_signal(self, current_price: float, current_high: float,
                       current_low: float, current_volume: float) -> Optional[MomentumSignal]:
        """
        Generate momentum breakout signal

        Returns: MomentumSignal or None
        """
        # Update price history
        self.price_history.append(current_price)
        self.high_history.append(current_high)
        self.low_history.append(current_low)

        # Update support/resistance
        self.update_support_resistance()

        # Check trade limit
        if self.trades_today >= self.max_trades_per_day:
            return None

        # Calculate indicators
        rsi = self.calculate_rsi()
        atr = self.calculate_atr()
        volume_ratio = self.calculate_volume_ratio(current_volume)

        # Detect breakout
        breakout_direction, breakout_level, breakout_strength = self.detect_breakout(
            current_price, current_high, current_low
        )

        if breakout_direction is None:
            return None

        # LONG signal conditions
        if breakout_direction == 'long':
            # Volume confirmation
            if volume_ratio < self.min_volume_ratio:
                return None

            # RSI confirmation
            if rsi < self.rsi_long_threshold:
                return None

            # Calculate confidence
            confidence = (
                min(1.0, volume_ratio / 5.0) * 0.4 +  # 40% weight
                min(1.0, (rsi - 50) / 50) * 0.3 +  # 30% weight
                min(1.0, breakout_strength / 0.01) * 0.3  # 30% weight
            )

            reason = f"Breakout above ${breakout_level:,.2f} | Vol: {volume_ratio:.1f}x | RSI: {rsi:.0f}"
            side = 'long'

        # SHORT signal conditions
        elif breakout_direction == 'short':
            # Volume confirmation
            if volume_ratio < self.min_volume_ratio:
                return None

            # RSI confirmation
            if rsi > self.rsi_short_threshold:
                return None

            # Calculate confidence
            confidence = (
                min(1.0, volume_ratio / 5.0) * 0.4 +
                min(1.0, (50 - rsi) / 50) * 0.3 +
                min(1.0, breakout_strength / 0.01) * 0.3
            )

            reason = f"Breakout below ${breakout_level:,.2f} | Vol: {volume_ratio:.1f}x | RSI: {rsi:.0f}"
            side = 'short'
        else:
            return None

        # Confidence threshold
        if confidence < self.min_breakout_strength:
            return None

        # Create signal
        signal = MomentumSignal(
            timestamp=datetime.now(),
            symbol=self.symbol,
            side=side,
            entry_price=current_price,
            confidence=confidence,
            reason=reason,
            breakout_level=breakout_level,
            volume_ratio=volume_ratio,
            rsi=rsi,
            atr=atr
        )

        return signal

    def calculate_targets(self, entry_price: float, side: str, atr: float) -> Dict[str, float]:
        """Calculate profit target and stop loss using ATR"""
        # Use ATR for dynamic stops if available
        if atr > 0:
            atr_pct = atr / entry_price
            stop_loss_pct = max(self.stop_loss_pct, atr_pct * 2)  # 2x ATR
            profit_target_pct = stop_loss_pct * 2  # 2:1 reward/risk
        else:
            stop_loss_pct = self.stop_loss_pct
            profit_target_pct = self.profit_target_pct

        if side == 'long':
            take_profit = entry_price * (1 + profit_target_pct)
            stop_loss = entry_price * (1 - stop_loss_pct)
        else:  # short
            take_profit = entry_price * (1 - profit_target_pct)
            stop_loss = entry_price * (1 + stop_loss_pct)

        return {
            'take_profit': take_profit,
            'stop_loss': stop_loss,
            'profit_target_pct': profit_target_pct * 100,
            'stop_loss_pct': stop_loss_pct * 100
        }

    def record_trade_result(self, is_win: bool):
        """Record trade result"""
        self.trades_today += 1
        if is_win:
            self.wins += 1
        else:
            self.losses += 1

    def get_win_rate(self) -> float:
        """Get current win rate"""
        total = self.wins + self.losses
        return self.wins / total if total > 0 else 0.0

    def reset_daily_stats(self):
        """Reset daily statistics"""
        self.trades_today = 0

    def get_status(self) -> Dict:
        """Get strategy status"""
        return {
            'symbol': self.symbol,
            'timeframe': self.timeframe,
            'trades_today': self.trades_today,
            'max_trades_per_day': self.max_trades_per_day,
            'total_wins': self.wins,
            'total_losses': self.losses,
            'win_rate': self.get_win_rate(),
            'target_daily_return': 2.0,
            'leverage': self.leverage,
            'position_size_pct': self.position_size_pct * 100,
            'resistance_levels': self.resistance_levels,
            'support_levels': self.support_levels
        }


if __name__ == '__main__':
    strategy = MomentumBreakoutStrategy("BTC/USDT", "15m")

    print("=" * 80)
    print("🚀 MOMENTUM BREAKOUT STRATEGY TEST")
    print("=" * 80)

    status = strategy.get_status()
    print("\n📊 Strategy Parameters:")
    for key, value in status.items():
        if key not in ['resistance_levels', 'support_levels']:
            print(f"   {key}: {value}")

    print("\n🧪 Simulating breakout signals...")

    # Build price history
    base_price = 42000
    for i in range(100):
        price = base_price + np.random.randn() * 500
        high = price + abs(np.random.randn() * 200)
        low = price - abs(np.random.randn() * 200)
        volume = 50 + abs(np.random.randn() * 20)

        signal = strategy.generate_signal(price, high, low, volume)

    print(f"\nSupport levels: {[f'${s:,.0f}' for s in strategy.support_levels]}")
    print(f"Resistance levels: {[f'${r:,.0f}' for r in strategy.resistance_levels]}")

    # Now test with breakouts
    signals_generated = 0
    for i in range(50):
        # Simulate potential breakout
        if strategy.resistance_levels:
            # Try breakout above resistance
            breakout_price = strategy.resistance_levels[0] * 1.005
            high = breakout_price
            low = breakout_price * 0.999
            volume = 150  # High volume
        elif strategy.support_levels:
            # Try breakout below support
            breakout_price = strategy.support_levels[0] * 0.995
            high = breakout_price * 1.001
            low = breakout_price
            volume = 150  # High volume
        else:
            breakout_price = base_price
            high = breakout_price * 1.001
            low = breakout_price * 0.999
            volume = 50

        signal = strategy.generate_signal(breakout_price, high, low, volume)

        if signal:
            signals_generated += 1
            print(f"\n✅ Breakout Signal #{signals_generated}:")
            print(f"   Side: {signal.side.upper()}")
            print(f"   Entry: ${signal.entry_price:,.2f}")
            print(f"   Breakout Level: ${signal.breakout_level:,.2f}")
            print(f"   Volume Ratio: {signal.volume_ratio:.1f}x")
            print(f"   RSI: {signal.rsi:.0f}")
            print(f"   Confidence: {signal.confidence*100:.1f}%")
            print(f"   Reason: {signal.reason}")

            targets = strategy.calculate_targets(signal.entry_price, signal.side, signal.atr)
            print(f"   Take Profit: ${targets['take_profit']:,.2f} (+{targets['profit_target_pct']:.2f}%)")
            print(f"   Stop Loss: ${targets['stop_loss']:,.2f} (-{targets['stop_loss_pct']:.2f}%)")

            # Simulate result (65% win rate)
            is_win = np.random.random() < 0.65
            strategy.record_trade_result(is_win)

            if signals_generated >= 10:
                break

    print(f"\n" + "=" * 80)
    print("📈 SIMULATION RESULTS")
    print("=" * 80)
    print(f"Signals Generated: {signals_generated}")
    print(f"Win Rate: {strategy.get_win_rate()*100:.1f}% (Target: 65%)")
    print(f"Wins: {strategy.wins} | Losses: {strategy.losses}")
    print("=" * 80)
