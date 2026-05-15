"""
GRID TRADING STRATEGY
Target: 0.8% daily return (8 trades/day @ 78% win rate)

Strategy Logic:
- Place buy/sell orders in a grid pattern
- Profit from range-bound price oscillations
- 0.18% profit per grid level
- Auto-rebalancing grid based on price movement
- 8x leverage on 8% position size

Grid Mechanism:
1. Define price range (support to resistance)
2. Create grid levels (10 levels)
3. Buy at lower levels, sell at upper levels
4. Profit from mean reversion within range
5. Disable in strong trends (trend filter)
"""

import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class GridLevel:
    """Grid price level"""
    price: float
    level_index: int  # 0 (bottom) to num_levels-1 (top)
    has_order: bool = False
    filled: bool = False


@dataclass
class GridSignal:
    """Grid trading signal"""
    timestamp: datetime
    symbol: str
    side: str  # 'buy' or 'sell'
    entry_price: float
    grid_level: int
    confidence: float
    reason: str


class GridTradingStrategy:
    """
    Grid trading for range-bound markets

    Target Performance:
    - 8 trades per day
    - 78% win rate
    - 0.18% avg profit per trade
    - 0.12% avg loss per trade
    - 0.8% daily return with 8x leverage
    """

    def __init__(self, symbol: str = "BTC/USDT"):
        self.symbol = symbol
        self.leverage = 8
        self.position_size_pct = 0.08  # 8% of capital

        # Grid parameters
        self.num_levels = 10
        self.grid_spacing_pct = 0.0018  # 0.18% between levels
        self.profit_per_level_pct = 0.0018  # 0.18% profit target

        # Grid state
        self.grid_levels: List[GridLevel] = []
        self.grid_center_price = 0
        self.grid_range_min = 0
        self.grid_range_max = 0

        # Market state
        self.is_ranging = True
        self.trend_direction = 'neutral'

        # Price history for trend detection
        self.price_history = []
        self.volume_history = []

        # Performance tracking
        self.trades_today = 0
        self.max_trades_per_day = 12
        self.wins = 0
        self.losses = 0

        # Open positions
        self.open_positions = []

    def detect_market_regime(self, current_price: float, current_volume: float) -> str:
        """
        Detect if market is ranging or trending

        Returns: 'ranging', 'trending_up', 'trending_down'
        """
        self.price_history.append(current_price)
        self.volume_history.append(current_volume)

        # Need enough data
        if len(self.price_history) < 50:
            return 'ranging'

        prices = self.price_history[-50:]

        # Calculate volatility
        returns = np.diff(prices) / prices[:-1]
        volatility = np.std(returns)

        # Calculate trend strength (linear regression slope)
        x = np.arange(len(prices))
        slope, _ = np.polyfit(x, prices, 1)
        slope_pct = (slope / np.mean(prices)) * 100

        # Determine regime
        if abs(slope_pct) < 0.1 and volatility < 0.02:
            # Low slope + low volatility = ranging
            self.is_ranging = True
            self.trend_direction = 'neutral'
            return 'ranging'

        elif slope_pct > 0.3:
            # Strong uptrend
            self.is_ranging = False
            self.trend_direction = 'up'
            return 'trending_up'

        elif slope_pct < -0.3:
            # Strong downtrend
            self.is_ranging = False
            self.trend_direction = 'down'
            return 'trending_down'

        else:
            # Weak trend = still rangeable
            self.is_ranging = True
            self.trend_direction = 'neutral'
            return 'ranging'

    def initialize_grid(self, center_price: float, range_pct: float = 0.02):
        """
        Initialize grid levels around center price

        range_pct: Total range as percentage (default 2% = ±1%)
        """
        self.grid_center_price = center_price
        self.grid_range_min = center_price * (1 - range_pct / 2)
        self.grid_range_max = center_price * (1 + range_pct / 2)

        # Create grid levels
        self.grid_levels = []
        price_range = self.grid_range_max - self.grid_range_min
        level_spacing = price_range / (self.num_levels - 1)

        for i in range(self.num_levels):
            level_price = self.grid_range_min + (i * level_spacing)
            self.grid_levels.append(GridLevel(
                price=level_price,
                level_index=i
            ))

        logger.info(f"Grid initialized: {len(self.grid_levels)} levels from ${self.grid_range_min:,.2f} to ${self.grid_range_max:,.2f}")

    def find_nearest_grid_level(self, current_price: float) -> Optional[GridLevel]:
        """Find the nearest grid level to current price"""
        if not self.grid_levels:
            return None

        nearest = min(self.grid_levels, key=lambda l: abs(l.price - current_price))
        return nearest

    def generate_signal(self, current_price: float, current_volume: float) -> Optional[GridSignal]:
        """
        Generate grid trading signal

        Returns: GridSignal or None
        """

        # Check trade limit
        if self.trades_today >= self.max_trades_per_day:
            return None

        # Detect market regime
        regime = self.detect_market_regime(current_price, current_volume)

        # Only trade in ranging markets
        if regime != 'ranging':
            logger.debug(f"Market is {regime}, grid trading disabled")
            return None

        # Initialize grid if not done
        if not self.grid_levels:
            self.initialize_grid(current_price)
            return None  # Wait for next candle

        # Check if price is outside grid range (rebalance needed)
        if current_price < self.grid_range_min or current_price > self.grid_range_max:
            logger.info(f"Price ${current_price:,.2f} outside grid range, rebalancing...")
            self.initialize_grid(current_price)
            return None

        # Find nearest grid level
        nearest_level = self.find_nearest_grid_level(current_price)

        if nearest_level is None:
            return None

        # Calculate distance to nearest level
        distance_pct = abs(current_price - nearest_level.price) / current_price

        # Only trade if very close to grid level (<0.05%)
        if distance_pct > 0.0005:
            return None

        # Determine signal direction based on grid position
        if nearest_level.level_index < self.num_levels / 2:
            # Lower half of grid = BUY
            side = 'buy'
            reason = f"Grid level {nearest_level.level_index + 1}/{self.num_levels} (lower range)"
        else:
            # Upper half of grid = SELL
            side = 'sell'
            reason = f"Grid level {nearest_level.level_index + 1}/{self.num_levels} (upper range)"

        # Calculate confidence based on position in grid
        # More confident at extremes
        distance_from_center = abs(nearest_level.level_index - self.num_levels / 2)
        confidence = 0.70 + (distance_from_center / self.num_levels) * 0.30
        confidence = min(0.95, confidence)

        # Create signal
        signal = GridSignal(
            timestamp=datetime.now(),
            symbol=self.symbol,
            side=side,
            entry_price=current_price,
            grid_level=nearest_level.level_index,
            confidence=confidence,
            reason=reason
        )

        return signal

    def calculate_targets(self, entry_price: float, side: str) -> Dict[str, float]:
        """Calculate take profit and stop loss for grid trade"""

        if side == 'buy':
            # Buy low, sell higher
            take_profit = entry_price * (1 + self.profit_per_level_pct)
            stop_loss = entry_price * (1 - self.profit_per_level_pct * 0.67)  # Tighter stop
        else:  # sell
            # Sell high, buy lower
            take_profit = entry_price * (1 - self.profit_per_level_pct)
            stop_loss = entry_price * (1 + self.profit_per_level_pct * 0.67)

        return {
            'take_profit': take_profit,
            'stop_loss': stop_loss,
            'profit_target_pct': self.profit_per_level_pct * 100,
            'stop_loss_pct': self.profit_per_level_pct * 0.67 * 100
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
            'trades_today': self.trades_today,
            'max_trades_per_day': self.max_trades_per_day,
            'total_wins': self.wins,
            'total_losses': self.losses,
            'win_rate': self.get_win_rate(),
            'target_daily_return': 0.8,
            'leverage': self.leverage,
            'position_size_pct': self.position_size_pct * 100,
            'is_ranging': self.is_ranging,
            'trend_direction': self.trend_direction,
            'grid_active': len(self.grid_levels) > 0,
            'num_grid_levels': len(self.grid_levels),
            'grid_range': f"${self.grid_range_min:,.0f} - ${self.grid_range_max:,.0f}" if self.grid_levels else "Not initialized"
        }


if __name__ == '__main__':
    strategy = GridTradingStrategy("BTC/USDT")

    print("=" * 80)
    print("📊 GRID TRADING STRATEGY TEST")
    print("=" * 80)

    status = strategy.get_status()
    print("\n📊 Strategy Parameters:")
    for key, value in status.items():
        print(f"   {key}: {value}")

    print("\n🧪 Simulating range-bound market...")

    # Simulate ranging market (oscillating between 41000-43000)
    base_price = 42000
    signals_generated = 0

    for i in range(200):
        # Simulate oscillating price
        t = i / 10
        oscillation = np.sin(t) * 1000  # ±$1000 oscillation
        noise = np.random.randn() * 200
        current_price = base_price + oscillation + noise

        current_volume = 50 + abs(np.random.randn() * 10)

        # Generate signal
        signal = strategy.generate_signal(current_price, current_volume)

        if signal:
            signals_generated += 1
            print(f"\n✅ Grid Signal #{signals_generated}:")
            print(f"   Side: {signal.side.upper()}")
            print(f"   Price: ${signal.entry_price:,.2f}")
            print(f"   Grid Level: {signal.grid_level + 1}/{strategy.num_levels}")
            print(f"   Confidence: {signal.confidence*100:.1f}%")
            print(f"   Reason: {signal.reason}")

            targets = strategy.calculate_targets(signal.entry_price, signal.side)
            print(f"   Take Profit: ${targets['take_profit']:,.2f} (+{targets['profit_target_pct']:.2f}%)")
            print(f"   Stop Loss: ${targets['stop_loss']:,.2f} (-{targets['stop_loss_pct']:.2f}%)")

            # Simulate result (78% win rate)
            is_win = np.random.random() < 0.78
            strategy.record_trade_result(is_win)

            if signals_generated >= 15:
                break

    print(f"\n" + "=" * 80)
    print("📈 SIMULATION RESULTS")
    print("=" * 80)
    print(f"Market Regime: {'RANGING ✅' if strategy.is_ranging else 'TRENDING ❌'}")
    print(f"Grid Status: {status['grid_range']}")
    print(f"Signals Generated: {signals_generated}")
    print(f"Win Rate: {strategy.get_win_rate()*100:.1f}% (Target: 78%)")
    print(f"Wins: {strategy.wins} | Losses: {strategy.losses}")
    print("=" * 80)
