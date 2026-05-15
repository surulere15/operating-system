"""
Trader Classification & Personalized Bot Configuration System
Specialized trading bot setups for every trader profile

Classifications:
1. Capital-Based Tiers (Micro → Whale)
2. Trading Style (Scalper → Position Trader)
3. Risk Profile (Conservative → Extreme)
4. Time Availability (Active → Passive)
5. Experience Level (Beginner → Professional)

Goal: Optimize performance for EVERY trader type with personalized configurations
"""

from enum import Enum
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# CLASSIFICATION ENUMS
# ============================================================================

class CapitalTier(Enum):
    """Capital-based classification"""
    MICRO = "micro"              # $100 - $1,000
    SMALL = "small"              # $1,000 - $5,000
    MEDIUM = "medium"            # $5,000 - $25,000
    LARGE = "large"              # $25,000 - $100,000
    WHALE = "whale"              # $100,000+


class TradingStyle(Enum):
    """Trading frequency and holding period"""
    SCALPER = "scalper"          # Minutes to hours, 20-100+ trades/day
    DAY_TRADER = "day_trader"    # Hours, 5-20 trades/day
    SWING_TRADER = "swing_trader"  # Days to weeks, 1-5 trades/week
    POSITION_TRADER = "position_trader"  # Weeks to months, 1-2 trades/month


class RiskProfile(Enum):
    """Risk tolerance"""
    CONSERVATIVE = "conservative"  # 0.5-1% risk per trade
    MODERATE = "moderate"          # 1-2% risk per trade
    AGGRESSIVE = "aggressive"      # 2-4% risk per trade
    EXTREME = "extreme"            # 4-10% risk per trade


class TimeAvailability(Enum):
    """Time commitment"""
    ACTIVE = "active"              # Full-time, 6-8+ hours/day
    PART_TIME = "part_time"        # 2-4 hours/day
    PASSIVE = "passive"            # <1 hour/day (set and forget)


class ExperienceLevel(Enum):
    """Trading experience"""
    BEGINNER = "beginner"          # 0-6 months
    INTERMEDIATE = "intermediate"  # 6 months - 2 years
    ADVANCED = "advanced"          # 2-5 years
    PROFESSIONAL = "professional"  # 5+ years


# ============================================================================
# TRADER PROFILE DATACLASS
# ============================================================================

@dataclass
class TraderProfile:
    """Complete trader profile"""
    user_id: int
    capital_tier: CapitalTier
    trading_style: TradingStyle
    risk_profile: RiskProfile
    time_availability: TimeAvailability
    experience_level: ExperienceLevel

    # Optional preferences
    preferred_symbols: List[str] = None
    preferred_exchanges: List[str] = None
    max_concurrent_trades: int = None

    def get_profile_code(self) -> str:
        """Get unique profile code (e.g., 'MEDIUM_SCALPER_AGGRESSIVE_ACTIVE_ADVANCED')"""
        return f"{self.capital_tier.value.upper()}_{self.trading_style.value.upper()}_{self.risk_profile.value.upper()}_{self.time_availability.value.upper()}_{self.experience_level.value.upper()}"


# ============================================================================
# BOT CONFIGURATION TEMPLATES
# ============================================================================

@dataclass
class BotConfiguration:
    """Optimized bot configuration for a trader profile"""
    profile_name: str
    description: str

    # Strategy settings
    recommended_strategy: str
    alternative_strategies: List[str]

    # Capital & risk
    min_capital: float
    recommended_capital: float
    position_size_percent: float
    risk_per_trade_percent: float
    max_concurrent_trades: int

    # Trade parameters
    stop_loss_percent: float
    take_profit_percent: float
    trailing_stop_percent: Optional[float]

    # Timing
    avg_trades_per_day: str
    avg_holding_period: str
    recommended_timeframes: List[str]

    # Features
    use_ml_predictions: bool
    use_sentiment_analysis: bool
    use_whale_tracking: bool
    use_smart_execution: bool
    use_leverage: bool
    max_leverage: float

    # Expected performance
    expected_monthly_return: str
    expected_win_rate: str
    expected_max_drawdown: str

    # Time commitment
    time_required_per_day: str
    automation_level: str  # Low, Medium, High, Full


# ============================================================================
# CAPITAL-BASED CONFIGURATIONS
# ============================================================================

class CapitalBasedConfigurations:
    """Configurations optimized by capital tier"""

    @staticmethod
    def get_micro_trader_config() -> BotConfiguration:
        """$100 - $1,000: Focus on consistent small gains, lower fees"""
        return BotConfiguration(
            profile_name="Micro Capital Trader",
            description="Optimized for small accounts: Low fees, high win rate, compound growth",

            recommended_strategy="ai_ensemble",
            alternative_strategies=["mean_reversion", "breakout"],

            min_capital=100,
            recommended_capital=500,
            position_size_percent=15.0,  # Smaller positions for safety
            risk_per_trade_percent=1.0,
            max_concurrent_trades=2,

            stop_loss_percent=2.0,
            take_profit_percent=3.0,  # Lower targets for quicker wins
            trailing_stop_percent=1.5,

            avg_trades_per_day="3-5",
            avg_holding_period="4-12 hours",
            recommended_timeframes=["15m", "1h", "4h"],

            use_ml_predictions=True,
            use_sentiment_analysis=True,
            use_whale_tracking=False,  # Less relevant for small caps
            use_smart_execution=False,  # Overhead not worth it
            use_leverage=False,
            max_leverage=1.0,

            expected_monthly_return="15-30%",
            expected_win_rate="70-75%",
            expected_max_drawdown="8-12%",

            time_required_per_day="1-2 hours",
            automation_level="High"
        )

    @staticmethod
    def get_small_trader_config() -> BotConfiguration:
        """$1,000 - $5,000: Balanced growth, moderate leverage"""
        return BotConfiguration(
            profile_name="Small Capital Trader",
            description="Balanced approach: Good diversification, moderate risk",

            recommended_strategy="ai_ensemble",
            alternative_strategies=["trend_following", "momentum"],

            min_capital=1000,
            recommended_capital=3000,
            position_size_percent=20.0,
            risk_per_trade_percent=2.0,
            max_concurrent_trades=4,

            stop_loss_percent=2.5,
            take_profit_percent=5.0,
            trailing_stop_percent=2.0,

            avg_trades_per_day="5-10",
            avg_holding_period="6-24 hours",
            recommended_timeframes=["1h", "4h"],

            use_ml_predictions=True,
            use_sentiment_analysis=True,
            use_whale_tracking=True,
            use_smart_execution=False,
            use_leverage=True,
            max_leverage=2.0,

            expected_monthly_return="25-50%",
            expected_win_rate="72-78%",
            expected_max_drawdown="10-15%",

            time_required_per_day="1-3 hours",
            automation_level="High"
        )

    @staticmethod
    def get_medium_trader_config() -> BotConfiguration:
        """$5,000 - $25,000: Aggressive growth, full features"""
        return BotConfiguration(
            profile_name="Medium Capital Trader",
            description="Aggressive growth: All features enabled, optimal diversification",

            recommended_strategy="ai_ensemble",
            alternative_strategies=["multi_strategy", "adaptive"],

            min_capital=5000,
            recommended_capital=15000,
            position_size_percent=25.0,
            risk_per_trade_percent=2.5,
            max_concurrent_trades=8,

            stop_loss_percent=3.0,
            take_profit_percent=6.0,
            trailing_stop_percent=2.5,

            avg_trades_per_day="10-20",
            avg_holding_period="12-48 hours",
            recommended_timeframes=["1h", "4h", "1d"],

            use_ml_predictions=True,
            use_sentiment_analysis=True,
            use_whale_tracking=True,
            use_smart_execution=True,
            use_leverage=True,
            max_leverage=3.0,

            expected_monthly_return="35-70%",
            expected_win_rate="75-80%",
            expected_max_drawdown="12-18%",

            time_required_per_day="2-4 hours",
            automation_level="Medium"
        )

    @staticmethod
    def get_large_trader_config() -> BotConfiguration:
        """$25,000 - $100,000: Institutional-grade execution"""
        return BotConfiguration(
            profile_name="Large Capital Trader",
            description="Institutional approach: Smart execution, low slippage, high volume",

            recommended_strategy="ai_ensemble",
            alternative_strategies=["multi_strategy", "arbitrage"],

            min_capital=25000,
            recommended_capital=50000,
            position_size_percent=30.0,
            risk_per_trade_percent=2.0,  # Lower risk % but larger $ amounts
            max_concurrent_trades=12,

            stop_loss_percent=2.5,
            take_profit_percent=5.0,
            trailing_stop_percent=2.0,

            avg_trades_per_day="15-30",
            avg_holding_period="1-3 days",
            recommended_timeframes=["4h", "1d"],

            use_ml_predictions=True,
            use_sentiment_analysis=True,
            use_whale_tracking=True,
            use_smart_execution=True,  # Critical for large orders
            use_leverage=True,
            max_leverage=2.0,  # Conservative leverage

            expected_monthly_return="25-50%",
            expected_win_rate="75-82%",
            expected_max_drawdown="10-15%",

            time_required_per_day="3-6 hours",
            automation_level="Medium"
        )

    @staticmethod
    def get_whale_trader_config() -> BotConfiguration:
        """$100,000+: Maximum sophistication, minimal slippage"""
        return BotConfiguration(
            profile_name="Whale Trader",
            description="Ultra-sophisticated: TWAP/VWAP execution, multi-exchange routing",

            recommended_strategy="ai_ensemble",
            alternative_strategies=["multi_strategy", "market_making"],

            min_capital=100000,
            recommended_capital=250000,
            position_size_percent=35.0,
            risk_per_trade_percent=1.5,  # Very conservative %
            max_concurrent_trades=15,

            stop_loss_percent=2.0,
            take_profit_percent=4.0,
            trailing_stop_percent=1.5,

            avg_trades_per_day="20-40",
            avg_holding_period="2-7 days",
            recommended_timeframes=["4h", "1d", "1w"],

            use_ml_predictions=True,
            use_sentiment_analysis=True,
            use_whale_tracking=True,
            use_smart_execution=True,  # Absolutely critical
            use_leverage=False,  # No need for leverage
            max_leverage=1.5,  # Very conservative if used

            expected_monthly_return="20-40%",
            expected_win_rate="78-85%",
            expected_max_drawdown="8-12%",

            time_required_per_day="4-8 hours",
            automation_level="Low"  # More manual oversight
        )


# ============================================================================
# TRADING STYLE CONFIGURATIONS
# ============================================================================

class TradingStyleConfigurations:
    """Configurations optimized by trading style"""

    @staticmethod
    def get_scalper_config() -> BotConfiguration:
        """Scalper: 20-100+ trades/day, minutes to hours"""
        return BotConfiguration(
            profile_name="Scalper",
            description="Ultra-high frequency: Quick in, quick out, small consistent gains",

            recommended_strategy="scalping",
            alternative_strategies=["momentum", "breakout"],

            min_capital=1000,
            recommended_capital=5000,
            position_size_percent=10.0,  # Small positions
            risk_per_trade_percent=0.5,  # Very tight risk
            max_concurrent_trades=3,  # Focus on quality

            stop_loss_percent=0.5,  # Tight stops
            take_profit_percent=1.0,  # Quick profits
            trailing_stop_percent=0.3,

            avg_trades_per_day="20-100+",
            avg_holding_period="5-60 minutes",
            recommended_timeframes=["1m", "5m", "15m"],

            use_ml_predictions=True,
            use_sentiment_analysis=False,  # Too slow
            use_whale_tracking=False,  # Not relevant
            use_smart_execution=False,  # Speed over optimization
            use_leverage=True,
            max_leverage=5.0,  # Higher leverage for small moves

            expected_monthly_return="30-60%",
            expected_win_rate="65-70%",  # Lower win rate, but many trades
            expected_max_drawdown="15-20%",

            time_required_per_day="6-8+ hours",
            automation_level="Medium"
        )

    @staticmethod
    def get_day_trader_config() -> BotConfiguration:
        """Day Trader: 5-20 trades/day, hours"""
        return BotConfiguration(
            profile_name="Day Trader",
            description="Active trading: Capitalize on daily volatility, close all by EOD",

            recommended_strategy="ai_ensemble",
            alternative_strategies=["momentum", "trend_following"],

            min_capital=2000,
            recommended_capital=10000,
            position_size_percent=20.0,
            risk_per_trade_percent=2.0,
            max_concurrent_trades=5,

            stop_loss_percent=2.0,
            take_profit_percent=4.0,
            trailing_stop_percent=1.5,

            avg_trades_per_day="5-20",
            avg_holding_period="1-8 hours",
            recommended_timeframes=["15m", "1h", "4h"],

            use_ml_predictions=True,
            use_sentiment_analysis=True,
            use_whale_tracking=True,
            use_smart_execution=True,
            use_leverage=True,
            max_leverage=3.0,

            expected_monthly_return="35-70%",
            expected_win_rate="72-78%",
            expected_max_drawdown="12-18%",

            time_required_per_day="4-6 hours",
            automation_level="High"
        )

    @staticmethod
    def get_swing_trader_config() -> BotConfiguration:
        """Swing Trader: 1-5 trades/week, days to weeks"""
        return BotConfiguration(
            profile_name="Swing Trader",
            description="Medium-term: Ride trends for days/weeks, fewer but larger moves",

            recommended_strategy="ai_ensemble",
            alternative_strategies=["trend_following", "breakout"],

            min_capital=5000,
            recommended_capital=20000,
            position_size_percent=30.0,
            risk_per_trade_percent=3.0,
            max_concurrent_trades=6,

            stop_loss_percent=4.0,
            take_profit_percent=10.0,  # Larger targets
            trailing_stop_percent=3.0,

            avg_trades_per_day="1-2",
            avg_holding_period="3-14 days",
            recommended_timeframes=["4h", "1d", "1w"],

            use_ml_predictions=True,
            use_sentiment_analysis=True,
            use_whale_tracking=True,
            use_smart_execution=True,
            use_leverage=True,
            max_leverage=2.0,

            expected_monthly_return="25-50%",
            expected_win_rate="75-82%",
            expected_max_drawdown="10-15%",

            time_required_per_day="1-2 hours",
            automation_level="High"
        )

    @staticmethod
    def get_position_trader_config() -> BotConfiguration:
        """Position Trader: 1-2 trades/month, weeks to months"""
        return BotConfiguration(
            profile_name="Position Trader",
            description="Long-term: Major trend following, minimal trading, max automation",

            recommended_strategy="ai_ensemble",
            alternative_strategies=["trend_following", "value"],

            min_capital=10000,
            recommended_capital=50000,
            position_size_percent=40.0,  # Larger positions
            risk_per_trade_percent=4.0,
            max_concurrent_trades=4,

            stop_loss_percent=8.0,  # Wide stops
            take_profit_percent=25.0,  # Large targets
            trailing_stop_percent=5.0,

            avg_trades_per_day="0.1-0.5",
            avg_holding_period="2-12 weeks",
            recommended_timeframes=["1d", "1w"],

            use_ml_predictions=True,
            use_sentiment_analysis=True,
            use_whale_tracking=True,
            use_smart_execution=True,
            use_leverage=False,  # Long-term, no leverage needed
            max_leverage=1.0,

            expected_monthly_return="15-35%",
            expected_win_rate="78-85%",
            expected_max_drawdown="8-12%",

            time_required_per_day="<1 hour",
            automation_level="Full"
        )


# ============================================================================
# INTELLIGENT PROFILE MATCHER
# ============================================================================

class TraderProfileMatcher:
    """
    Intelligently matches trader to optimal bot configuration
    """

    def __init__(self):
        self.capital_configs = CapitalBasedConfigurations()
        self.style_configs = TradingStyleConfigurations()

    def get_optimal_configuration(self, profile: TraderProfile) -> BotConfiguration:
        """
        Get optimal bot configuration for trader profile

        Args:
            profile: Trader profile

        Returns:
            Optimal bot configuration
        """
        # Start with capital-based config
        base_config = self._get_capital_config(profile.capital_tier)

        # Adjust for trading style
        style_adjustments = self._get_style_adjustments(profile.trading_style)

        # Adjust for risk profile
        risk_adjustments = self._get_risk_adjustments(profile.risk_profile)

        # Adjust for experience level
        experience_adjustments = self._get_experience_adjustments(profile.experience_level)

        # Merge all adjustments
        final_config = self._merge_configurations(
            base_config,
            style_adjustments,
            risk_adjustments,
            experience_adjustments
        )

        logger.info(f"🎯 Matched profile {profile.get_profile_code()} to configuration: {final_config.profile_name}")

        return final_config

    def _get_capital_config(self, tier: CapitalTier) -> BotConfiguration:
        """Get base config by capital tier"""
        configs = {
            CapitalTier.MICRO: self.capital_configs.get_micro_trader_config(),
            CapitalTier.SMALL: self.capital_configs.get_small_trader_config(),
            CapitalTier.MEDIUM: self.capital_configs.get_medium_trader_config(),
            CapitalTier.LARGE: self.capital_configs.get_large_trader_config(),
            CapitalTier.WHALE: self.capital_configs.get_whale_trader_config()
        }
        return configs[tier]

    def _get_style_adjustments(self, style: TradingStyle) -> Dict:
        """Get adjustments based on trading style"""
        style_configs = {
            TradingStyle.SCALPER: self.style_configs.get_scalper_config(),
            TradingStyle.DAY_TRADER: self.style_configs.get_day_trader_config(),
            TradingStyle.SWING_TRADER: self.style_configs.get_swing_trader_config(),
            TradingStyle.POSITION_TRADER: self.style_configs.get_position_trader_config()
        }

        config = style_configs[style]

        return {
            'avg_trades_per_day': config.avg_trades_per_day,
            'avg_holding_period': config.avg_holding_period,
            'recommended_timeframes': config.recommended_timeframes,
            'stop_loss_percent': config.stop_loss_percent,
            'take_profit_percent': config.take_profit_percent,
            'automation_level': config.automation_level
        }

    def _get_risk_adjustments(self, risk: RiskProfile) -> Dict:
        """Get adjustments based on risk profile"""
        risk_multipliers = {
            RiskProfile.CONSERVATIVE: {
                'risk_per_trade_percent': 0.5,
                'position_size_multiplier': 0.6,
                'max_leverage': 1.0,
                'max_concurrent_trades_multiplier': 0.7
            },
            RiskProfile.MODERATE: {
                'risk_per_trade_percent': 2.0,
                'position_size_multiplier': 1.0,
                'max_leverage': 2.0,
                'max_concurrent_trades_multiplier': 1.0
            },
            RiskProfile.AGGRESSIVE: {
                'risk_per_trade_percent': 4.0,
                'position_size_multiplier': 1.4,
                'max_leverage': 3.5,
                'max_concurrent_trades_multiplier': 1.3
            },
            RiskProfile.EXTREME: {
                'risk_per_trade_percent': 8.0,
                'position_size_multiplier': 1.8,
                'max_leverage': 5.0,
                'max_concurrent_trades_multiplier': 1.5
            }
        }

        return risk_multipliers[risk]

    def _get_experience_adjustments(self, experience: ExperienceLevel) -> Dict:
        """Get adjustments based on experience level"""
        experience_settings = {
            ExperienceLevel.BEGINNER: {
                'use_leverage': False,
                'max_leverage': 1.0,
                'automation_level': 'Full',
                'max_concurrent_trades_multiplier': 0.5,
                'safety_features': 'Maximum'
            },
            ExperienceLevel.INTERMEDIATE: {
                'use_leverage': True,
                'max_leverage': 2.0,
                'automation_level': 'High',
                'max_concurrent_trades_multiplier': 0.8,
                'safety_features': 'High'
            },
            ExperienceLevel.ADVANCED: {
                'use_leverage': True,
                'max_leverage': 3.0,
                'automation_level': 'Medium',
                'max_concurrent_trades_multiplier': 1.0,
                'safety_features': 'Moderate'
            },
            ExperienceLevel.PROFESSIONAL: {
                'use_leverage': True,
                'max_leverage': 5.0,
                'automation_level': 'Low',
                'max_concurrent_trades_multiplier': 1.2,
                'safety_features': 'Minimal'
            }
        }

        return experience_settings[experience]

    def _merge_configurations(
        self,
        base: BotConfiguration,
        style: Dict,
        risk: Dict,
        experience: Dict
    ) -> BotConfiguration:
        """Merge all configuration adjustments"""

        # Apply style adjustments
        base.avg_trades_per_day = style['avg_trades_per_day']
        base.avg_holding_period = style['avg_holding_period']
        base.recommended_timeframes = style['recommended_timeframes']
        base.automation_level = style['automation_level']

        # Apply risk adjustments
        base.risk_per_trade_percent = risk['risk_per_trade_percent']
        base.position_size_percent *= risk['position_size_multiplier']
        base.max_concurrent_trades = int(base.max_concurrent_trades * risk['max_concurrent_trades_multiplier'])

        # Apply experience adjustments
        base.use_leverage = experience['use_leverage']
        base.max_leverage = min(base.max_leverage, experience['max_leverage'])
        base.max_concurrent_trades = int(base.max_concurrent_trades * experience['max_concurrent_trades_multiplier'])

        return base


# ============================================================================
# SPECIALIZED TEMPLATES (PRE-CONFIGURED PERSONAS)
# ============================================================================

class SpecializedTemplates:
    """Pre-configured templates for common trader personas"""

    @staticmethod
    def get_all_templates() -> Dict[str, Dict]:
        """Get all specialized templates"""
        return {
            'hourly_earner': {
                'name': '⚡ Hourly Earner',
                'description': 'Maximize hourly earnings with ultra-high frequency scalping',
                'target_audience': 'Active traders seeking consistent hourly income',
                'capital_requirement': '$2,000+',
                'time_commitment': '6-8 hours/day',
                'profile': TraderProfile(
                    user_id=0,
                    capital_tier=CapitalTier.SMALL,
                    trading_style=TradingStyle.SCALPER,
                    risk_profile=RiskProfile.AGGRESSIVE,
                    time_availability=TimeAvailability.ACTIVE,
                    experience_level=ExperienceLevel.INTERMEDIATE
                ),
                'expected_hourly_earnings': '$50-200/hour',
                'expected_daily_earnings': '$300-1,600/day',
                'expected_monthly_return': '40-80%'
            },

            'daily_earner': {
                'name': '💰 Daily Earner',
                'description': 'Consistent daily profits with day trading',
                'target_audience': 'Part-time traders seeking daily income',
                'capital_requirement': '$5,000+',
                'time_commitment': '4-6 hours/day',
                'profile': TraderProfile(
                    user_id=0,
                    capital_tier=CapitalTier.MEDIUM,
                    trading_style=TradingStyle.DAY_TRADER,
                    risk_profile=RiskProfile.MODERATE,
                    time_availability=TimeAvailability.PART_TIME,
                    experience_level=ExperienceLevel.INTERMEDIATE
                ),
                'expected_daily_earnings': '$200-1,000/day',
                'expected_monthly_return': '30-60%'
            },

            'passive_income': {
                'name': '😴 Passive Income',
                'description': 'Set and forget swing trading for busy professionals',
                'target_audience': 'Busy professionals, minimal time commitment',
                'capital_requirement': '$10,000+',
                'time_commitment': '<1 hour/day',
                'profile': TraderProfile(
                    user_id=0,
                    capital_tier=CapitalTier.MEDIUM,
                    trading_style=TradingStyle.SWING_TRADER,
                    risk_profile=RiskProfile.CONSERVATIVE,
                    time_availability=TimeAvailability.PASSIVE,
                    experience_level=ExperienceLevel.BEGINNER
                ),
                'expected_monthly_return': '20-40%'
            },

            'wealth_builder': {
                'name': '🏆 Wealth Builder',
                'description': 'Long-term compound growth for serious capital',
                'target_audience': 'Large capital investors seeking steady growth',
                'capital_requirement': '$50,000+',
                'time_commitment': '2-3 hours/day',
                'profile': TraderProfile(
                    user_id=0,
                    capital_tier=CapitalTier.LARGE,
                    trading_style=TradingStyle.POSITION_TRADER,
                    risk_profile=RiskProfile.MODERATE,
                    time_availability=TimeAvailability.PART_TIME,
                    experience_level=ExperienceLevel.ADVANCED
                ),
                'expected_monthly_return': '15-35%',
                'compound_projection_12mo': '$50k → $220k (340% growth)'
            },

            'beginner_safe': {
                'name': '🛡️ Beginner Safe',
                'description': 'Maximum safety with full automation for beginners',
                'target_audience': 'Complete beginners, risk-averse',
                'capital_requirement': '$500+',
                'time_commitment': '30 min/day',
                'profile': TraderProfile(
                    user_id=0,
                    capital_tier=CapitalTier.SMALL,
                    trading_style=TradingStyle.SWING_TRADER,
                    risk_profile=RiskProfile.CONSERVATIVE,
                    time_availability=TimeAvailability.PASSIVE,
                    experience_level=ExperienceLevel.BEGINNER
                ),
                'expected_monthly_return': '10-25%',
                'max_drawdown': '5-8%'
            },

            'professional_trader': {
                'name': '🎯 Professional Trader',
                'description': 'Full-featured institutional-grade setup',
                'target_audience': 'Experienced traders, full-time commitment',
                'capital_requirement': '$25,000+',
                'time_commitment': '8+ hours/day',
                'profile': TraderProfile(
                    user_id=0,
                    capital_tier=CapitalTier.LARGE,
                    trading_style=TradingStyle.DAY_TRADER,
                    risk_profile=RiskProfile.AGGRESSIVE,
                    time_availability=TimeAvailability.ACTIVE,
                    experience_level=ExperienceLevel.PROFESSIONAL
                ),
                'expected_monthly_return': '50-100%',
                'expected_sharpe_ratio': '4.5-6.0'
            },

            'whale_institutional': {
                'name': '🐋 Whale / Institutional',
                'description': 'Ultra-sophisticated setup for massive capital',
                'target_audience': 'Institutional investors, high net worth',
                'capital_requirement': '$100,000+',
                'time_commitment': 'Managed service available',
                'profile': TraderProfile(
                    user_id=0,
                    capital_tier=CapitalTier.WHALE,
                    trading_style=TradingStyle.POSITION_TRADER,
                    risk_profile=RiskProfile.MODERATE,
                    time_availability=TimeAvailability.PART_TIME,
                    experience_level=ExperienceLevel.PROFESSIONAL
                ),
                'expected_monthly_return': '20-50%',
                'white_glove_service': True
            }
        }


# ============================================================================
# PROFILE WIZARD
# ============================================================================

class ProfileWizard:
    """Interactive wizard to determine optimal trader profile"""

    def __init__(self):
        self.matcher = TraderProfileMatcher()

    def quick_profile_from_capital_and_time(
        self,
        capital: float,
        hours_per_day: float,
        risk_tolerance: str = "moderate"
    ) -> Tuple[TraderProfile, BotConfiguration]:
        """
        Quick profile creation from basic inputs

        Args:
            capital: Trading capital in USD
            hours_per_day: Hours available per day
            risk_tolerance: 'conservative', 'moderate', 'aggressive', 'extreme'

        Returns:
            (TraderProfile, BotConfiguration)
        """

        # Determine capital tier
        if capital < 1000:
            capital_tier = CapitalTier.MICRO
        elif capital < 5000:
            capital_tier = CapitalTier.SMALL
        elif capital < 25000:
            capital_tier = CapitalTier.MEDIUM
        elif capital < 100000:
            capital_tier = CapitalTier.LARGE
        else:
            capital_tier = CapitalTier.WHALE

        # Determine trading style from time availability
        if hours_per_day >= 6:
            trading_style = TradingStyle.SCALPER
            time_availability = TimeAvailability.ACTIVE
        elif hours_per_day >= 3:
            trading_style = TradingStyle.DAY_TRADER
            time_availability = TimeAvailability.PART_TIME
        elif hours_per_day >= 1:
            trading_style = TradingStyle.SWING_TRADER
            time_availability = TimeAvailability.PART_TIME
        else:
            trading_style = TradingStyle.POSITION_TRADER
            time_availability = TimeAvailability.PASSIVE

        # Map risk tolerance
        risk_map = {
            'conservative': RiskProfile.CONSERVATIVE,
            'moderate': RiskProfile.MODERATE,
            'aggressive': RiskProfile.AGGRESSIVE,
            'extreme': RiskProfile.EXTREME
        }
        risk_profile = risk_map.get(risk_tolerance.lower(), RiskProfile.MODERATE)

        # Assume intermediate for quick setup
        experience_level = ExperienceLevel.INTERMEDIATE

        # Create profile
        profile = TraderProfile(
            user_id=0,
            capital_tier=capital_tier,
            trading_style=trading_style,
            risk_profile=risk_profile,
            time_availability=time_availability,
            experience_level=experience_level
        )

        # Get optimal config
        config = self.matcher.get_optimal_configuration(profile)

        logger.info(f"✅ Quick profile created for ${capital:,.0f} capital, {hours_per_day}h/day")
        logger.info(f"   Profile: {profile.get_profile_code()}")
        logger.info(f"   Config: {config.profile_name}")

        return profile, config

    def get_template_config(self, template_name: str) -> Tuple[TraderProfile, BotConfiguration]:
        """
        Get configuration from specialized template

        Args:
            template_name: Template name (e.g., 'hourly_earner', 'passive_income')

        Returns:
            (TraderProfile, BotConfiguration)
        """
        templates = SpecializedTemplates.get_all_templates()

        if template_name not in templates:
            raise ValueError(f"Template '{template_name}' not found")

        template = templates[template_name]
        profile = template['profile']
        config = self.matcher.get_optimal_configuration(profile)

        logger.info(f"✅ Loaded template: {template['name']}")

        return profile, config


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

def example_usage():
    """Example usage of trader classification system"""

    wizard = ProfileWizard()

    # Example 1: Quick profile from capital and time
    print("\n" + "="*80)
    print("EXAMPLE 1: Quick Profile Creation")
    print("="*80)

    profile1, config1 = wizard.quick_profile_from_capital_and_time(
        capital=5000,
        hours_per_day=4,
        risk_tolerance="aggressive"
    )

    print(f"\nProfile: {profile1.get_profile_code()}")
    print(f"Config: {config1.profile_name}")
    print(f"Expected Monthly Return: {config1.expected_monthly_return}")
    print(f"Time Required: {config1.time_required_per_day}")

    # Example 2: Specialized template
    print("\n" + "="*80)
    print("EXAMPLE 2: Hourly Earner Template")
    print("="*80)

    profile2, config2 = wizard.get_template_config('hourly_earner')

    print(f"\nProfile: {profile2.get_profile_code()}")
    print(f"Config: {config2.profile_name}")
    print(f"Avg Trades/Day: {config2.avg_trades_per_day}")
    print(f"Expected Monthly Return: {config2.expected_monthly_return}")

    # Example 3: All templates
    print("\n" + "="*80)
    print("EXAMPLE 3: All Available Templates")
    print("="*80)

    templates = SpecializedTemplates.get_all_templates()
    for name, template in templates.items():
        print(f"\n{template['name']}")
        print(f"  Target: {template['target_audience']}")
        print(f"  Capital: {template['capital_requirement']}")
        print(f"  Time: {template['time_commitment']}")
        print(f"  Returns: {template.get('expected_monthly_return', 'N/A')}")


if __name__ == "__main__":
    example_usage()
