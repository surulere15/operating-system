"""
Trading Strategies Collection
Multiple algorithmic trading strategies for different market conditions
"""

import numpy as np
from typing import Dict, List, Tuple
import logging
from abc import ABC, abstractmethod

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TradingStrategy(ABC):
    """Base class for all trading strategies"""

    def __init__(self, config: Dict):
        self.config = config

    @abstractmethod
    def generate_signal(self, ohlcv: List, current_price: float) -> Dict:
        """
        Generate trading signal
        Returns: {'action': 'buy'|'sell'|'hold', 'confidence': 0-100, 'reason': str}
        """
        pass

    @staticmethod
    def _calculate_sma(data: np.ndarray, period: int) -> np.ndarray:
        """Calculate Simple Moving Average"""
        sma = np.convolve(data, np.ones(period), 'valid') / period
        return np.concatenate([np.full(period - 1, np.nan), sma])

    @staticmethod
    def _calculate_ema(data: np.ndarray, period: int) -> np.ndarray:
        """Calculate Exponential Moving Average"""
        ema = np.zeros_like(data)
        multiplier = 2 / (period + 1)
        ema[0] = data[0]

        for i in range(1, len(data)):
            ema[i] = (data[i] * multiplier) + (ema[i-1] * (1 - multiplier))

        return ema

    @staticmethod
    def _calculate_rsi(data: np.ndarray, period: int = 14) -> np.ndarray:
        """Calculate Relative Strength Index"""
        deltas = np.diff(data)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        avg_gains = np.convolve(gains, np.ones(period), 'valid') / period
        avg_losses = np.convolve(losses, np.ones(period), 'valid') / period

        rs = np.divide(avg_gains, avg_losses, where=avg_losses != 0)
        rsi = 100 - (100 / (1 + rs))

        return np.concatenate([np.full(period, np.nan), rsi])

    @staticmethod
    def _calculate_macd(data: np.ndarray, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Calculate MACD (Moving Average Convergence Divergence)
        Returns: (macd_line, signal_line, histogram)
        """
        ema_fast = TradingStrategy._calculate_ema(data, fast)
        ema_slow = TradingStrategy._calculate_ema(data, slow)
        macd_line = ema_fast - ema_slow
        signal_line = TradingStrategy._calculate_ema(macd_line, signal)
        histogram = macd_line - signal_line

        return macd_line, signal_line, histogram


# ============================================================================
# STRATEGY 1: MA CROSSOVER (Current Strategy)
# ============================================================================

class MACrossoverStrategy(TradingStrategy):
    """
    Moving Average Crossover Strategy

    Buy: Fast MA crosses above Slow MA
    Sell: Fast MA crosses below Slow MA

    Confirmation: RSI + Volume
    """

    def generate_signal(self, ohlcv: List, current_price: float) -> Dict:
        try:
            if len(ohlcv) < 50:
                return {'action': 'hold', 'confidence': 0, 'reason': 'Insufficient data'}

            closes = np.array([x[4] for x in ohlcv])
            volumes = np.array([x[5] for x in ohlcv])

            # Calculate indicators
            fast_period = self.config.get('ma_fast_period', 9)
            slow_period = self.config.get('ma_slow_period', 21)

            sma_fast = self._calculate_sma(closes, fast_period)
            sma_slow = self._calculate_sma(closes, slow_period)
            rsi = self._calculate_rsi(closes, 14)

            volume_avg = np.mean(volumes[-20:])
            current_volume = volumes[-1]

            # Current and previous values
            current_sma_fast = sma_fast[-1]
            current_sma_slow = sma_slow[-1]
            current_rsi = rsi[-1]
            prev_sma_fast = sma_fast[-2]
            prev_sma_slow = sma_slow[-2]

            # BULLISH SIGNAL
            if prev_sma_fast <= prev_sma_slow and current_sma_fast > current_sma_slow:
                confidence = 50
                reasons = []

                if 30 <= current_rsi <= 70:
                    confidence += 20
                    reasons.append(f"RSI neutral ({current_rsi:.1f})")
                elif current_rsi < 30:
                    confidence += 30
                    reasons.append(f"RSI oversold ({current_rsi:.1f})")

                if current_volume > volume_avg * 1.2:
                    confidence += 15
                    reasons.append("Strong volume")

                return {
                    'action': 'buy',
                    'confidence': min(confidence, 100),
                    'reason': f"Bullish MA crossover. {', '.join(reasons)}"
                }

            # BEARISH SIGNAL
            elif prev_sma_fast >= prev_sma_slow and current_sma_fast < current_sma_slow:
                confidence = 50
                reasons = []

                if 30 <= current_rsi <= 70:
                    confidence += 20
                    reasons.append(f"RSI neutral ({current_rsi:.1f})")
                elif current_rsi > 70:
                    confidence += 30
                    reasons.append(f"RSI overbought ({current_rsi:.1f})")

                if current_volume > volume_avg * 1.2:
                    confidence += 15
                    reasons.append("Strong volume")

                return {
                    'action': 'sell',
                    'confidence': min(confidence, 100),
                    'reason': f"Bearish MA crossover. {', '.join(reasons)}"
                }

            return {'action': 'hold', 'confidence': 0, 'reason': 'No crossover detected'}

        except Exception as e:
            logger.error(f"MA Crossover error: {str(e)}")
            return {'action': 'hold', 'confidence': 0, 'reason': f'Error: {str(e)}'}


# ============================================================================
# STRATEGY 2: GRID TRADING
# ============================================================================

class GridTradingStrategy(TradingStrategy):
    """
    Grid Trading Strategy

    Creates a grid of buy/sell orders at predetermined price levels.
    Buy when price drops to lower grid line, sell when it rises to upper grid line.

    Best for: Sideways/ranging markets
    """

    def __init__(self, config: Dict):
        super().__init__(config)
        self.grid_levels = config.get('grid_levels', 10)  # Number of grid lines
        self.grid_range_percent = config.get('grid_range_percent', 5)  # % range from current price
        self.last_trade_price = None

    def generate_signal(self, ohlcv: List, current_price: float) -> Dict:
        try:
            if len(ohlcv) < 20:
                return {'action': 'hold', 'confidence': 0, 'reason': 'Insufficient data'}

            closes = np.array([x[4] for x in ohlcv])

            # Calculate grid boundaries
            avg_price = np.mean(closes[-20:])
            upper_bound = avg_price * (1 + self.grid_range_percent / 100)
            lower_bound = avg_price * (1 - self.grid_range_percent / 100)

            # Calculate grid step
            grid_step = (upper_bound - lower_bound) / self.grid_levels

            # Determine current position in grid
            position_in_grid = (current_price - lower_bound) / grid_step

            # BUY SIGNAL: Price near lower grid lines
            if position_in_grid <= 3:  # Bottom 30% of grid
                confidence = 70 + int((3 - position_in_grid) * 10)  # Higher confidence at lower prices
                return {
                    'action': 'buy',
                    'confidence': min(confidence, 100),
                    'reason': f"Grid buy at level {position_in_grid:.1f}/{self.grid_levels} (${current_price:.2f})"
                }

            # SELL SIGNAL: Price near upper grid lines
            elif position_in_grid >= 7:  # Top 30% of grid
                confidence = 70 + int((position_in_grid - 7) * 10)
                return {
                    'action': 'sell',
                    'confidence': min(confidence, 100),
                    'reason': f"Grid sell at level {position_in_grid:.1f}/{self.grid_levels} (${current_price:.2f})"
                }

            return {
                'action': 'hold',
                'confidence': 0,
                'reason': f"Price in middle grid (level {position_in_grid:.1f})"
            }

        except Exception as e:
            logger.error(f"Grid Trading error: {str(e)}")
            return {'action': 'hold', 'confidence': 0, 'reason': f'Error: {str(e)}'}


# ============================================================================
# STRATEGY 3: DCA (Dollar Cost Averaging)
# ============================================================================

class DCAStrategy(TradingStrategy):
    """
    Dollar Cost Averaging Strategy

    Buys fixed dollar amount at regular intervals regardless of price.
    Sells when target profit is reached.

    Best for: Long-term accumulation, reducing timing risk
    """

    def __init__(self, config: Dict):
        super().__init__(config)
        self.buy_interval = config.get('dca_interval_hours', 24)  # Hours between buys
        self.profit_target = config.get('dca_profit_target', 10)  # % profit to sell
        self.last_buy_time = None
        self.avg_entry_price = None

    def generate_signal(self, ohlcv: List, current_price: float) -> Dict:
        try:
            if len(ohlcv) < 10:
                return {'action': 'hold', 'confidence': 0, 'reason': 'Insufficient data'}

            closes = np.array([x[4] for x in ohlcv])

            # Calculate trend using longer-term MA
            sma_50 = self._calculate_sma(closes, min(50, len(closes) - 1))
            current_sma = sma_50[-1] if len(sma_50) > 0 else current_price

            # BUY SIGNAL: Regular DCA buy (check if interval passed)
            # In real implementation, would check actual time elapsed
            # For now, use RSI as a bonus timing indicator
            rsi = self._calculate_rsi(closes, 14)
            current_rsi = rsi[-1]

            # DCA buys more aggressively when price is below MA (dip buying)
            if current_price < current_sma:
                confidence = 80
                reason = f"DCA buy (price below MA: ${current_price:.2f} vs ${current_sma:.2f})"

                if current_rsi < 40:
                    confidence = 90
                    reason += ", RSI oversold"

                return {
                    'action': 'buy',
                    'confidence': confidence,
                    'reason': reason
                }

            # Regular DCA buy
            elif current_rsi < 60:  # Don't buy when very overbought
                return {
                    'action': 'buy',
                    'confidence': 70,
                    'reason': f"Regular DCA buy at ${current_price:.2f}"
                }

            # SELL SIGNAL: Check if profit target reached
            # This would compare to avg_entry_price in real implementation
            if current_rsi > 75:  # Very overbought
                return {
                    'action': 'sell',
                    'confidence': 80,
                    'reason': f"Take profit - RSI overbought ({current_rsi:.1f})"
                }

            return {
                'action': 'hold',
                'confidence': 0,
                'reason': 'Waiting for DCA interval or profit target'
            }

        except Exception as e:
            logger.error(f"DCA Strategy error: {str(e)}")
            return {'action': 'hold', 'confidence': 0, 'reason': f'Error: {str(e)}'}


# ============================================================================
# STRATEGY 4: MACD
# ============================================================================

class MACDStrategy(TradingStrategy):
    """
    MACD (Moving Average Convergence Divergence) Strategy

    Buy: MACD line crosses above signal line (bullish crossover)
    Sell: MACD line crosses below signal line (bearish crossover)

    Confirmation: Histogram strength, RSI

    Best for: Trend following, momentum trading
    """

    def generate_signal(self, ohlcv: List, current_price: float) -> Dict:
        try:
            if len(ohlcv) < 50:
                return {'action': 'hold', 'confidence': 0, 'reason': 'Insufficient data'}

            closes = np.array([x[4] for x in ohlcv])
            volumes = np.array([x[5] for x in ohlcv])

            # Calculate MACD
            fast = self.config.get('macd_fast', 12)
            slow = self.config.get('macd_slow', 26)
            signal_period = self.config.get('macd_signal', 9)

            macd_line, signal_line, histogram = self._calculate_macd(closes, fast, slow, signal_period)
            rsi = self._calculate_rsi(closes, 14)

            volume_avg = np.mean(volumes[-20:])
            current_volume = volumes[-1]

            # Current and previous values
            current_macd = macd_line[-1]
            current_signal = signal_line[-1]
            current_histogram = histogram[-1]
            current_rsi = rsi[-1]

            prev_macd = macd_line[-2]
            prev_signal = signal_line[-2]
            prev_histogram = histogram[-2]

            # BULLISH SIGNAL: MACD crosses above signal
            if prev_macd <= prev_signal and current_macd > current_signal:
                confidence = 55
                reasons = []

                # Histogram strength (stronger signal if histogram increasing)
                if current_histogram > prev_histogram:
                    confidence += 15
                    reasons.append("Increasing momentum")

                # RSI confirmation
                if 30 <= current_rsi <= 70:
                    confidence += 15
                    reasons.append(f"RSI neutral ({current_rsi:.1f})")
                elif current_rsi < 30:
                    confidence += 20
                    reasons.append(f"RSI oversold ({current_rsi:.1f})")

                # Volume confirmation
                if current_volume > volume_avg * 1.2:
                    confidence += 10
                    reasons.append("Strong volume")

                return {
                    'action': 'buy',
                    'confidence': min(confidence, 100),
                    'reason': f"Bullish MACD crossover. {', '.join(reasons)}"
                }

            # BEARISH SIGNAL: MACD crosses below signal
            elif prev_macd >= prev_signal and current_macd < current_signal:
                confidence = 55
                reasons = []

                # Histogram strength
                if abs(current_histogram) > abs(prev_histogram):
                    confidence += 15
                    reasons.append("Increasing bearish momentum")

                # RSI confirmation
                if 30 <= current_rsi <= 70:
                    confidence += 15
                    reasons.append(f"RSI neutral ({current_rsi:.1f})")
                elif current_rsi > 70:
                    confidence += 20
                    reasons.append(f"RSI overbought ({current_rsi:.1f})")

                # Volume confirmation
                if current_volume > volume_avg * 1.2:
                    confidence += 10
                    reasons.append("Strong volume")

                return {
                    'action': 'sell',
                    'confidence': min(confidence, 100),
                    'reason': f"Bearish MACD crossover. {', '.join(reasons)}"
                }

            return {
                'action': 'hold',
                'confidence': 0,
                'reason': 'No MACD crossover detected'
            }

        except Exception as e:
            logger.error(f"MACD Strategy error: {str(e)}")
            return {'action': 'hold', 'confidence': 0, 'reason': f'Error: {str(e)}'}


# ============================================================================
# STRATEGY FACTORY
# ============================================================================

class StrategyFactory:
    """Factory to create strategy instances"""

    STRATEGIES = {
        'ma_crossover': MACrossoverStrategy,
        'grid': GridTradingStrategy,
        'dca': DCAStrategy,
        'macd': MACDStrategy
    }

    @staticmethod
    def create_strategy(strategy_name: str, config: Dict) -> TradingStrategy:
        """
        Create a strategy instance

        Args:
            strategy_name: Name of strategy ('ma_crossover', 'grid', 'dca', 'macd')
            config: Strategy configuration

        Returns:
            TradingStrategy instance
        """
        strategy_class = StrategyFactory.STRATEGIES.get(strategy_name.lower())

        if not strategy_class:
            logger.warning(f"Unknown strategy: {strategy_name}, defaulting to MA Crossover")
            strategy_class = MACrossoverStrategy

        return strategy_class(config)

    @staticmethod
    def get_available_strategies() -> List[Dict]:
        """Get list of available strategies with descriptions"""
        return [
            {
                'id': 'ma_crossover',
                'name': 'MA Crossover',
                'description': 'Moving Average crossover with RSI and volume confirmation',
                'best_for': 'Trending markets',
                'risk_level': 'Medium',
                'timeframe': '15m - 4h'
            },
            {
                'id': 'grid',
                'name': 'Grid Trading',
                'description': 'Buy low, sell high within a price range',
                'best_for': 'Sideways/ranging markets',
                'risk_level': 'Low-Medium',
                'timeframe': '1h - 1d'
            },
            {
                'id': 'dca',
                'name': 'Dollar Cost Averaging',
                'description': 'Regular buys to accumulate over time',
                'best_for': 'Long-term accumulation',
                'risk_level': 'Low',
                'timeframe': '1d - 1w'
            },
            {
                'id': 'macd',
                'name': 'MACD',
                'description': 'MACD crossover with histogram and RSI confirmation',
                'best_for': 'Momentum trading',
                'risk_level': 'Medium-High',
                'timeframe': '15m - 4h'
            }
        ]
