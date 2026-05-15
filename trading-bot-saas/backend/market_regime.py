"""
Adaptive Market Regime Detection System
Automatically adjusts strategies based on market conditions

Market Regimes:
- Bull Market (strong uptrend)
- Bear Market (strong downtrend)
- Sideways/Range (consolidation)
- High Volatility (choppy)
- Low Volatility (calm)
- Crash (extreme downward movement)
- Moon (extreme upward movement)

Features:
- Real-time regime detection
- Automatic strategy switching
- Volatility-adaptive position sizing
- Risk adjustment based on conditions
- Performance tracking per regime

Goal: Optimize performance in ALL market conditions
"""

from enum import Enum
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import logging
from collections import deque

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MarketRegime(Enum):
    """Market regime types"""
    BULL_MARKET = "bull_market"
    BEAR_MARKET = "bear_market"
    SIDEWAYS = "sideways"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"
    CRASH = "crash"
    MOON = "moon"


@dataclass
class RegimeConfig:
    """Configuration for each market regime"""
    regime: MarketRegime
    recommended_strategy: str
    position_size_multiplier: float
    max_concurrent_trades: int
    stop_loss_multiplier: float
    take_profit_multiplier: float
    use_leverage: bool
    description: str


class MarketRegimeDetector:
    """
    Detects current market regime using multiple indicators
    """

    def __init__(self, symbol: str):
        self.symbol = symbol
        self.price_history = deque(maxlen=100)
        self.volume_history = deque(maxlen=100)

    def detect_regime(self, price_data: List[float], volume_data: List[float] = None) -> Dict:
        """
        Detect current market regime

        Args:
            price_data: Recent price data (last 100 periods)
            volume_data: Optional volume data

        Returns:
            Regime information with confidence
        """
        if len(price_data) < 20:
            return {
                'regime': MarketRegime.SIDEWAYS.value,
                'confidence': 0.5,
                'message': 'Insufficient data for reliable detection'
            }

        # Calculate indicators
        returns = self._calculate_returns(price_data)
        volatility = self._calculate_volatility(returns)
        trend_strength = self._calculate_trend_strength(price_data)
        momentum = self._calculate_momentum(price_data)

        # Detect regime
        regime, confidence = self._classify_regime(
            returns,
            volatility,
            trend_strength,
            momentum
        )

        logger.info(f"📊 Market Regime: {regime.value.upper()} (confidence: {confidence:.1%})")

        return {
            'regime': regime.value,
            'confidence': confidence,
            'indicators': {
                'avg_return': sum(returns[-20:]) / 20 if returns else 0,
                'volatility': volatility,
                'trend_strength': trend_strength,
                'momentum': momentum
            },
            'description': self._get_regime_description(regime),
            'detected_at': datetime.utcnow().isoformat()
        }

    def _calculate_returns(self, prices: List[float]) -> List[float]:
        """Calculate percentage returns"""
        returns = []
        for i in range(1, len(prices)):
            ret = (prices[i] - prices[i-1]) / prices[i-1]
            returns.append(ret)
        return returns

    def _calculate_volatility(self, returns: List[float]) -> float:
        """Calculate volatility (standard deviation of returns)"""
        if len(returns) < 2:
            return 0.0

        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        return variance ** 0.5

    def _calculate_trend_strength(self, prices: List[float]) -> float:
        """
        Calculate trend strength (-1 to +1)
        Positive = uptrend, Negative = downtrend
        """
        if len(prices) < 20:
            return 0.0

        # Simple trend: compare recent vs older prices
        recent_avg = sum(prices[-10:]) / 10
        older_avg = sum(prices[-20:-10]) / 10

        if older_avg == 0:
            return 0.0

        trend = (recent_avg - older_avg) / older_avg
        return max(-1, min(1, trend * 10))  # Normalize to -1 to +1

    def _calculate_momentum(self, prices: List[float]) -> float:
        """Calculate price momentum"""
        if len(prices) < 10:
            return 0.0

        momentum = (prices[-1] - prices[-10]) / prices[-10]
        return momentum

    def _classify_regime(
        self,
        returns: List[float],
        volatility: float,
        trend_strength: float,
        momentum: float
    ) -> Tuple[MarketRegime, float]:
        """
        Classify market regime based on indicators

        Returns:
            (regime, confidence)
        """
        # Calculate average return
        avg_return = sum(returns[-20:]) / 20 if len(returns) >= 20 else 0

        # Extreme movements (Crash or Moon)
        if avg_return < -0.05:  # -5% average return
            return MarketRegime.CRASH, 0.9

        if avg_return > 0.05:  # +5% average return
            return MarketRegime.MOON, 0.9

        # High volatility regime
        if volatility > 0.03:  # 3% daily volatility
            return MarketRegime.HIGH_VOLATILITY, 0.8

        # Low volatility regime
        if volatility < 0.01:  # 1% daily volatility
            return MarketRegime.LOW_VOLATILITY, 0.8

        # Trend-based regimes
        if trend_strength > 0.3 and avg_return > 0.01:
            return MarketRegime.BULL_MARKET, 0.85

        if trend_strength < -0.3 and avg_return < -0.01:
            return MarketRegime.BEAR_MARKET, 0.85

        # Default to sideways
        return MarketRegime.SIDEWAYS, 0.7

    def _get_regime_description(self, regime: MarketRegime) -> str:
        """Get description of regime"""
        descriptions = {
            MarketRegime.BULL_MARKET: "Strong upward trend - good for long positions",
            MarketRegime.BEAR_MARKET: "Strong downward trend - consider shorts or stay out",
            MarketRegime.SIDEWAYS: "Range-bound market - mean reversion strategies work best",
            MarketRegime.HIGH_VOLATILITY: "Choppy market - reduce position sizes",
            MarketRegime.LOW_VOLATILITY: "Calm market - can increase position sizes",
            MarketRegime.CRASH: "Extreme downward movement - RISK OFF",
            MarketRegime.MOON: "Extreme upward movement - ride the trend carefully"
        }
        return descriptions.get(regime, "Unknown regime")


class AdaptiveStrategySelector:
    """
    Automatically selects and adjusts strategies based on market regime
    """

    def __init__(self):
        # Define optimal configuration for each regime
        self.regime_configs = {
            MarketRegime.BULL_MARKET: RegimeConfig(
                regime=MarketRegime.BULL_MARKET,
                recommended_strategy='trend_following',
                position_size_multiplier=1.2,
                max_concurrent_trades=8,
                stop_loss_multiplier=1.0,
                take_profit_multiplier=1.5,
                use_leverage=True,
                description='Aggressive long positions'
            ),
            MarketRegime.BEAR_MARKET: RegimeConfig(
                regime=MarketRegime.BEAR_MARKET,
                recommended_strategy='short_selling',
                position_size_multiplier=0.8,
                max_concurrent_trades=5,
                stop_loss_multiplier=1.2,
                take_profit_multiplier=1.0,
                use_leverage=False,
                description='Defensive positioning or shorts'
            ),
            MarketRegime.SIDEWAYS: RegimeConfig(
                regime=MarketRegime.SIDEWAYS,
                recommended_strategy='mean_reversion',
                position_size_multiplier=1.0,
                max_concurrent_trades=6,
                stop_loss_multiplier=0.8,
                take_profit_multiplier=0.8,
                use_leverage=False,
                description='Range trading strategies'
            ),
            MarketRegime.HIGH_VOLATILITY: RegimeConfig(
                regime=MarketRegime.HIGH_VOLATILITY,
                recommended_strategy='scalping',
                position_size_multiplier=0.5,
                max_concurrent_trades=3,
                stop_loss_multiplier=1.5,
                take_profit_multiplier=0.5,
                use_leverage=False,
                description='Reduced risk, quick trades'
            ),
            MarketRegime.LOW_VOLATILITY: RegimeConfig(
                regime=MarketRegime.LOW_VOLATILITY,
                recommended_strategy='breakout',
                position_size_multiplier=1.5,
                max_concurrent_trades=10,
                stop_loss_multiplier=0.8,
                take_profit_multiplier=2.0,
                use_leverage=True,
                description='Anticipate breakouts'
            ),
            MarketRegime.CRASH: RegimeConfig(
                regime=MarketRegime.CRASH,
                recommended_strategy='cash',
                position_size_multiplier=0.0,
                max_concurrent_trades=0,
                stop_loss_multiplier=2.0,
                take_profit_multiplier=1.0,
                use_leverage=False,
                description='RISK OFF - Preserve capital'
            ),
            MarketRegime.MOON: RegimeConfig(
                regime=MarketRegime.MOON,
                recommended_strategy='momentum',
                position_size_multiplier=1.5,
                max_concurrent_trades=10,
                stop_loss_multiplier=1.5,
                take_profit_multiplier=2.0,
                use_leverage=True,
                description='Ride the momentum'
            )
        }

    def get_optimal_config(self, regime: str, base_config: Dict) -> Dict:
        """
        Get optimal configuration for detected regime

        Args:
            regime: Detected market regime
            base_config: Base trading configuration

        Returns:
            Adjusted configuration
        """
        regime_enum = MarketRegime(regime)
        regime_config = self.regime_configs[regime_enum]

        # Adjust base config based on regime
        adjusted_config = base_config.copy()

        adjusted_config.update({
            'position_size': base_config.get('position_size', 100) * regime_config.position_size_multiplier,
            'max_concurrent_trades': regime_config.max_concurrent_trades,
            'stop_loss_percent': base_config.get('stop_loss_percent', 2.0) * regime_config.stop_loss_multiplier,
            'take_profit_percent': base_config.get('take_profit_percent', 4.0) * regime_config.take_profit_multiplier,
            'use_leverage': regime_config.use_leverage,
            'recommended_strategy': regime_config.recommended_strategy,
            'regime_description': regime_config.description
        })

        logger.info(f"⚙️ Config adjusted for {regime.upper()}")
        logger.info(f"  Position size: {adjusted_config['position_size']:.1f}")
        logger.info(f"  Max trades: {adjusted_config['max_concurrent_trades']}")
        logger.info(f"  Strategy: {adjusted_config['recommended_strategy']}")

        return adjusted_config


class AdaptiveTradingSystem:
    """
    Complete adaptive trading system

    Features:
    - Real-time regime detection
    - Automatic strategy switching
    - Risk adjustment
    - Performance tracking per regime
    """

    def __init__(self, symbol: str):
        self.symbol = symbol
        self.detector = MarketRegimeDetector(symbol)
        self.selector = AdaptiveStrategySelector()
        self.current_regime = None
        self.regime_history = []
        self.performance_by_regime = {}

    async def analyze_and_adapt(self, price_data: List[float], current_config: Dict) -> Dict:
        """
        Analyze market and adapt configuration

        Args:
            price_data: Recent price data
            current_config: Current trading configuration

        Returns:
            Adapted configuration with regime info
        """
        # Detect regime
        regime_info = self.detector.detect_regime(price_data)
        detected_regime = regime_info['regime']

        # Check if regime changed
        if detected_regime != self.current_regime:
            logger.info(f"🔄 Regime Change: {self.current_regime or 'UNKNOWN'} → {detected_regime}")

            self.current_regime = detected_regime
            self.regime_history.append({
                'regime': detected_regime,
                'timestamp': datetime.utcnow().isoformat(),
                'confidence': regime_info['confidence']
            })

        # Get optimal configuration for this regime
        adapted_config = self.selector.get_optimal_config(detected_regime, current_config)

        return {
            'regime_info': regime_info,
            'adapted_config': adapted_config,
            'regime_changed': len(self.regime_history) > 0 and self.regime_history[-1]['regime'] == detected_regime,
            'recommendations': self._get_recommendations(detected_regime, regime_info['confidence'])
        }

    def _get_recommendations(self, regime: str, confidence: float) -> List[str]:
        """Get actionable recommendations for current regime"""
        recommendations = {
            'bull_market': [
                "✅ Increase long positions",
                "✅ Use trailing stops to lock profits",
                "✅ Consider using moderate leverage",
                "⚠️ Watch for exhaustion signals"
            ],
            'bear_market': [
                "⚠️ Reduce position sizes",
                "⚠️ Consider hedging or shorting",
                "✅ Keep cash reserves",
                "✅ Wait for reversal signals"
            ],
            'sideways': [
                "✅ Use range trading strategies",
                "✅ Buy support, sell resistance",
                "✅ Tight stop losses",
                "⚠️ Avoid breakout strategies"
            ],
            'high_volatility': [
                "⚠️ REDUCE risk - cut position sizes in half",
                "⚠️ Wider stop losses to avoid whipsaw",
                "✅ Take profits quickly",
                "⚠️ Avoid leverage"
            ],
            'low_volatility': [
                "✅ Can increase position sizes",
                "✅ Good time for larger positions",
                "✅ Anticipate breakout",
                "✅ Monitor volume for breakout confirmation"
            ],
            'crash': [
                "🚨 RISK OFF - Exit all positions",
                "🚨 Preserve capital",
                "🚨 Do NOT try to catch falling knife",
                "✅ Wait for stabilization"
            ],
            'moon': [
                "🚀 Ride the trend with trailing stops",
                "⚠️ Don't get greedy - take profits",
                "⚠️ Watch for exhaustion",
                "✅ Let winners run"
            ]
        }

        return recommendations.get(regime, ["Monitor market conditions"])

    def get_performance_summary(self) -> Dict:
        """Get performance summary by regime"""
        return {
            'current_regime': self.current_regime,
            'regime_changes_today': len([
                r for r in self.regime_history
                if datetime.fromisoformat(r['timestamp']) > datetime.utcnow() - timedelta(days=1)
            ]),
            'regime_history': self.regime_history[-10:],  # Last 10 regime changes
            'performance_by_regime': self.performance_by_regime
        }


# Example usage
async def adaptive_trading_example():
    """Example of adaptive trading system"""
    system = AdaptiveTradingSystem("BTC/USDT")

    # Simulate price data
    price_data = [50000 + i * 100 for i in range(100)]  # Uptrend

    # Current config
    current_config = {
        'position_size': 1000,
        'stop_loss_percent': 2.0,
        'take_profit_percent': 4.0,
        'max_concurrent_trades': 5
    }

    # Analyze and adapt
    result = await system.analyze_and_adapt(price_data, current_config)

    print(f"Regime: {result['regime_info']['regime']}")
    print(f"Confidence: {result['regime_info']['confidence']:.1%}")
    print(f"Adapted position size: {result['adapted_config']['position_size']}")
    print(f"Recommendations: {result['recommendations']}")
