"""
Dynamic Position Sizing - Consistency Through Risk Management
The difference between consistent profits and account blow-ups

PROBLEM:
- Fixed position sizes ignore signal quality
- No adjustment for winning/losing streaks
- Same size during high volatility vs low volatility
- No consideration of current drawdown

SOLUTION:
- Scale position by signal confidence
- Reduce size during drawdown
- Adjust for market volatility
- Enforce maximum risk limits

This prevents the #1 cause of trading failure: OVER-LEVERAGING
"""

import logging
from typing import Optional, Dict, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import math

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS
# ============================================================================

class PositionSizeAdjustment(Enum):
    """Reasons for position size adjustment"""
    CONFIDENCE_SCALE = "confidence_scale"  # Based on signal confidence
    DRAWDOWN_REDUCE = "drawdown_reduce"  # Reduce during drawdown
    VOLATILITY_ADJUST = "volatility_adjust"  # Adjust for market volatility
    STREAK_CAUTION = "streak_caution"  # Reduce after losing streak
    WIN_STREAK_SCALE = "win_streak_scale"  # Increase after winning streak
    MAX_RISK_LIMIT = "max_risk_limit"  # Hard risk limit


class MarketRegime(Enum):
    """Market volatility regime"""
    LOW_VOL = "low_volatility"  # VIX < 15
    NORMAL_VOL = "normal_volatility"  # VIX 15-25
    HIGH_VOL = "high_volatility"  # VIX 25-35
    EXTREME_VOL = "extreme_volatility"  # VIX > 35


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class PositionSizeDecision:
    """
    Documents why a position size was chosen
    TRANSPARENCY - Know exactly why each size was selected
    """
    symbol: str
    base_size: float  # What you WOULD trade without adjustments
    final_size: float  # What you ACTUALLY trade

    # Adjustments applied
    confidence_multiplier: float = 1.0
    drawdown_multiplier: float = 1.0
    volatility_multiplier: float = 1.0
    streak_multiplier: float = 1.0

    # Context
    signal_confidence: float = 0.0
    current_drawdown_pct: float = 0.0
    market_regime: MarketRegime = MarketRegime.NORMAL_VOL
    consecutive_losses: int = 0

    # Risk metrics
    risk_per_trade: float = 0.0  # As % of capital
    max_risk_allowed: float = 0.02  # 2% default

    # Reasoning
    adjustments: list = None

    def __post_init__(self):
        if self.adjustments is None:
            self.adjustments = []

    def calculate_total_multiplier(self) -> float:
        """Total multiplier applied"""
        return (
            self.confidence_multiplier *
            self.drawdown_multiplier *
            self.volatility_multiplier *
            self.streak_multiplier
        )

    def add_adjustment(self, adjustment_type: PositionSizeAdjustment, multiplier: float, reason: str):
        """Record an adjustment"""
        self.adjustments.append({
            'type': adjustment_type.value,
            'multiplier': multiplier,
            'reason': reason
        })

    def get_reasoning_summary(self) -> str:
        """Human-readable summary of sizing decision"""
        summary = f"Position Size: {self.final_size:.4f} (from base {self.base_size:.4f})\n"
        summary += f"Total Multiplier: {self.calculate_total_multiplier():.2f}x\n"
        summary += "\nAdjustments Applied:\n"

        for adj in self.adjustments:
            summary += f"  - {adj['type']}: {adj['multiplier']:.2f}x ({adj['reason']})\n"

        return summary


# ============================================================================
# DYNAMIC POSITION SIZER
# ============================================================================

class DynamicPositionSizer:
    """
    Calculates position sizes dynamically based on multiple factors
    THE KEY TO CONSISTENCY: Right-size every trade
    """

    def __init__(
        self,
        base_capital: float,
        base_position_pct: float = 0.02,  # 2% of capital per trade
        max_risk_pct: float = 0.02,  # 2% max risk per trade
        max_drawdown_threshold: float = 0.15,  # 15% max drawdown
    ):
        """
        Initialize position sizer

        Args:
            base_capital: Total trading capital
            base_position_pct: Base position size as % of capital
            max_risk_pct: Maximum risk per trade (% of capital)
            max_drawdown_threshold: Max drawdown before reducing size
        """
        self.base_capital = base_capital
        self.current_capital = base_capital
        self.base_position_pct = base_position_pct
        self.max_risk_pct = max_risk_pct
        self.max_drawdown_threshold = max_drawdown_threshold

        # State tracking
        self.peak_capital = base_capital
        self.current_drawdown = 0.0
        self.consecutive_losses = 0
        self.consecutive_wins = 0
        self.recent_win_rate = 0.5  # Start at 50%

        logger.info("✅ Dynamic Position Sizer initialized")
        logger.info(f"   Base capital: ${base_capital:,.0f}")
        logger.info(f"   Base position: {base_position_pct:.1%}")
        logger.info(f"   Max risk: {max_risk_pct:.1%}")
        logger.info(f"   Max drawdown: {max_drawdown_threshold:.1%}")

    def calculate_position_size(
        self,
        symbol: str,
        signal_confidence: float,
        expected_return: float,
        market_volatility: float,
        stop_loss_pct: Optional[float] = None
    ) -> PositionSizeDecision:
        """
        Calculate optimal position size for trade

        Args:
            symbol: Trading symbol
            signal_confidence: 0.0-1.0 confidence score
            expected_return: Expected return % (e.g., 0.02 = 2%)
            market_volatility: Current volatility measure
            stop_loss_pct: Stop loss as % (e.g., 0.02 = 2%)

        Returns:
            PositionSizeDecision with size and reasoning
        """
        # Base position size
        base_size = self.current_capital * self.base_position_pct

        # Initialize decision
        decision = PositionSizeDecision(
            symbol=symbol,
            base_size=base_size,
            final_size=base_size,
            signal_confidence=signal_confidence,
            current_drawdown_pct=self.current_drawdown,
            consecutive_losses=self.consecutive_losses
        )

        # Apply adjustments
        decision = self._adjust_for_confidence(decision, signal_confidence)
        decision = self._adjust_for_drawdown(decision)
        decision = self._adjust_for_volatility(decision, market_volatility)
        decision = self._adjust_for_streak(decision)
        decision = self._enforce_risk_limits(decision, stop_loss_pct)

        # Calculate final size
        total_multiplier = decision.calculate_total_multiplier()
        decision.final_size = base_size * total_multiplier

        # Calculate risk
        if stop_loss_pct:
            decision.risk_per_trade = decision.final_size * stop_loss_pct / self.current_capital

        # Log decision
        logger.info(f"📊 Position sizing for {symbol}:")
        logger.info(f"   Base: ${base_size:.2f}")
        logger.info(f"   Final: ${decision.final_size:.2f} ({total_multiplier:.2f}x)")
        logger.info(f"   Risk: {decision.risk_per_trade:.2%}")

        return decision

    def _adjust_for_confidence(self, decision: PositionSizeDecision, confidence: float) -> PositionSizeDecision:
        """
        Scale position by signal confidence
        High confidence = larger size, Low confidence = smaller size
        """
        if confidence >= 0.8:
            # High confidence: 1.5x size
            multiplier = 1.5
            reason = f"High confidence ({confidence:.0%})"
        elif confidence >= 0.6:
            # Medium confidence: 1.0x size (no change)
            multiplier = 1.0
            reason = f"Medium confidence ({confidence:.0%})"
        else:
            # Low confidence: 0.5x size
            multiplier = 0.5
            reason = f"Low confidence ({confidence:.0%})"

        decision.confidence_multiplier = multiplier
        decision.add_adjustment(PositionSizeAdjustment.CONFIDENCE_SCALE, multiplier, reason)

        return decision

    def _adjust_for_drawdown(self, decision: PositionSizeDecision) -> PositionSizeDecision:
        """
        Reduce size during drawdowns
        CRITICAL: Prevents compounding losses
        """
        if self.current_drawdown == 0:
            # No drawdown
            multiplier = 1.0
            reason = "No active drawdown"
        elif self.current_drawdown < 0.05:
            # Small drawdown (<5%): 0.9x
            multiplier = 0.9
            reason = f"Small drawdown ({self.current_drawdown:.1%})"
        elif self.current_drawdown < 0.10:
            # Medium drawdown (5-10%): 0.7x
            multiplier = 0.7
            reason = f"Medium drawdown ({self.current_drawdown:.1%})"
        elif self.current_drawdown < self.max_drawdown_threshold:
            # Large drawdown (10-15%): 0.5x
            multiplier = 0.5
            reason = f"Large drawdown ({self.current_drawdown:.1%})"
        else:
            # Max drawdown exceeded: 0.25x (defensive)
            multiplier = 0.25
            reason = f"MAX drawdown exceeded ({self.current_drawdown:.1%})"
            logger.warning(f"⚠️ Maximum drawdown exceeded: {self.current_drawdown:.1%}")

        decision.drawdown_multiplier = multiplier
        decision.add_adjustment(PositionSizeAdjustment.DRAWDOWN_REDUCE, multiplier, reason)

        return decision

    def _adjust_for_volatility(self, decision: PositionSizeDecision, volatility: float) -> PositionSizeDecision:
        """
        Adjust for market volatility
        High volatility = smaller size (more risk)
        """
        # Determine market regime
        if volatility < 0.15:
            regime = MarketRegime.LOW_VOL
            multiplier = 1.2  # Low vol: 1.2x size
        elif volatility < 0.25:
            regime = MarketRegime.NORMAL_VOL
            multiplier = 1.0  # Normal vol: 1.0x size
        elif volatility < 0.35:
            regime = MarketRegime.HIGH_VOL
            multiplier = 0.7  # High vol: 0.7x size
        else:
            regime = MarketRegime.EXTREME_VOL
            multiplier = 0.4  # Extreme vol: 0.4x size
            logger.warning(f"⚠️ Extreme volatility detected: {volatility:.1%}")

        decision.market_regime = regime
        decision.volatility_multiplier = multiplier
        decision.add_adjustment(
            PositionSizeAdjustment.VOLATILITY_ADJUST,
            multiplier,
            f"{regime.value} (vol={volatility:.1%})"
        )

        return decision

    def _adjust_for_streak(self, decision: PositionSizeDecision) -> PositionSizeDecision:
        """
        Adjust for winning/losing streaks
        Losing streak = reduce size (avoid revenge trading)
        Winning streak = cautious increase (avoid overconfidence)
        """
        if self.consecutive_losses >= 5:
            # Long losing streak: 0.5x (DEFENSIVE)
            multiplier = 0.5
            reason = f"{self.consecutive_losses} consecutive losses - reduce size"
            logger.warning(f"⚠️ Losing streak: {self.consecutive_losses} trades")

        elif self.consecutive_losses >= 3:
            # Medium losing streak: 0.7x
            multiplier = 0.7
            reason = f"{self.consecutive_losses} consecutive losses - caution"

        elif self.consecutive_wins >= 5:
            # Long winning streak: 1.2x (slight increase, avoid overconfidence)
            multiplier = 1.2
            reason = f"{self.consecutive_wins} consecutive wins - cautious increase"

        elif self.consecutive_wins >= 3:
            # Medium winning streak: 1.1x
            multiplier = 1.1
            reason = f"{self.consecutive_wins} consecutive wins - slight increase"

        else:
            # No significant streak
            multiplier = 1.0
            reason = "No significant streak"

        decision.streak_multiplier = multiplier
        decision.add_adjustment(PositionSizeAdjustment.STREAK_CAUTION, multiplier, reason)

        return decision

    def _enforce_risk_limits(self, decision: PositionSizeDecision, stop_loss_pct: Optional[float]) -> PositionSizeDecision:
        """
        Enforce maximum risk per trade
        HARD LIMIT - Never risk more than max_risk_pct
        """
        if not stop_loss_pct:
            return decision

        # Calculate current risk
        current_risk = decision.final_size * stop_loss_pct / self.current_capital

        # If risk exceeds max, reduce position size
        if current_risk > self.max_risk_pct:
            # Calculate reduction needed
            multiplier = self.max_risk_pct / current_risk

            decision.final_size *= multiplier
            reason = f"Risk limit: reduced from {current_risk:.2%} to {self.max_risk_pct:.2%}"
            decision.add_adjustment(PositionSizeAdjustment.MAX_RISK_LIMIT, multiplier, reason)

            logger.warning(f"⚠️ Risk limit enforced: {current_risk:.2%} > {self.max_risk_pct:.2%}")

        decision.risk_per_trade = min(current_risk, self.max_risk_pct)
        decision.max_risk_allowed = self.max_risk_pct

        return decision

    def update_after_trade(self, trade_pnl: float, was_winner: bool):
        """
        Update state after trade closes

        Args:
            trade_pnl: Trade profit/loss in dollars
            was_winner: True if winning trade
        """
        # Update capital
        self.current_capital += trade_pnl

        # Update peak
        if self.current_capital > self.peak_capital:
            self.peak_capital = self.current_capital

        # Update drawdown
        self.current_drawdown = (self.peak_capital - self.current_capital) / self.peak_capital

        # Update streaks
        if was_winner:
            self.consecutive_wins += 1
            self.consecutive_losses = 0
        else:
            self.consecutive_losses += 1
            self.consecutive_wins = 0

        # Log state
        logger.info(f"📊 Capital: ${self.current_capital:,.0f} (DD: {self.current_drawdown:.1%})")
        logger.info(f"   Streak: {self.consecutive_wins}W / {self.consecutive_losses}L")

    def reset_peak(self):
        """Reset peak capital (new high)"""
        self.peak_capital = self.current_capital
        self.current_drawdown = 0.0
        logger.info(f"✅ New peak capital: ${self.peak_capital:,.0f}")

    def get_status(self) -> Dict:
        """Get current position sizing status"""
        return {
            "base_capital": self.base_capital,
            "current_capital": self.current_capital,
            "peak_capital": self.peak_capital,
            "current_drawdown": self.current_drawdown,
            "consecutive_wins": self.consecutive_wins,
            "consecutive_losses": self.consecutive_losses,
            "base_position_size": self.current_capital * self.base_position_pct,
            "max_risk_per_trade": self.max_risk_pct
        }


# ============================================================================
# KELLY CRITERION POSITION SIZER (Advanced)
# ============================================================================

class KellyPositionSizer:
    """
    Kelly Criterion for optimal position sizing
    More aggressive but mathematically optimal
    """

    def __init__(self, fraction: float = 0.25):
        """
        Initialize Kelly sizer

        Args:
            fraction: Kelly fraction (0.25 = quarter Kelly, safer)
        """
        self.fraction = fraction
        logger.info(f"✅ Kelly Position Sizer initialized (fraction: {fraction})")

    def calculate_kelly_size(
        self,
        win_rate: float,
        avg_win: float,
        avg_loss: float,
        capital: float
    ) -> float:
        """
        Calculate Kelly optimal position size

        Formula: Kelly% = (Win% * AvgWin - Loss% * AvgLoss) / AvgWin

        Args:
            win_rate: Historical win rate (0.0-1.0)
            avg_win: Average winning trade %
            avg_loss: Average losing trade %
            capital: Current capital

        Returns:
            Position size in dollars
        """
        loss_rate = 1 - win_rate

        # Kelly formula
        kelly_pct = (win_rate * avg_win - loss_rate * avg_loss) / avg_win

        # Apply fraction (quarter Kelly safer)
        fractional_kelly = kelly_pct * self.fraction

        # Ensure positive and bounded
        fractional_kelly = max(0.0, min(fractional_kelly, 0.25))  # Cap at 25%

        position_size = capital * fractional_kelly

        logger.info(f"📊 Kelly sizing:")
        logger.info(f"   Full Kelly: {kelly_pct:.1%}")
        logger.info(f"   Fractional: {fractional_kelly:.1%}")
        logger.info(f"   Position: ${position_size:.2f}")

        return position_size


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

def example_usage():
    print("\n" + "="*80)
    print("DYNAMIC POSITION SIZING - DEMO")
    print("="*80)

    # Initialize sizer
    sizer = DynamicPositionSizer(
        base_capital=100000,
        base_position_pct=0.02,  # 2%
        max_risk_pct=0.02
    )

    print("\n📊 Scenario 1: High confidence, normal conditions")
    decision = sizer.calculate_position_size(
        symbol="BTC/USDT",
        signal_confidence=0.85,  # High confidence
        expected_return=0.02,
        market_volatility=0.20,  # Normal vol
        stop_loss_pct=0.02
    )
    print(decision.get_reasoning_summary())

    # Simulate losing trade
    sizer.update_after_trade(-200, was_winner=False)

    print("\n📊 Scenario 2: After losing trade")
    decision = sizer.calculate_position_size(
        symbol="ETH/USDT",
        signal_confidence=0.75,
        expected_return=0.015,
        market_volatility=0.20,
        stop_loss_pct=0.02
    )
    print(decision.get_reasoning_summary())

    # Simulate 5 more losses (losing streak)
    for _ in range(4):
        sizer.update_after_trade(-150, was_winner=False)

    print("\n📊 Scenario 3: During losing streak + drawdown")
    decision = sizer.calculate_position_size(
        symbol="SOL/USDT",
        signal_confidence=0.80,
        expected_return=0.025,
        market_volatility=0.30,  # High vol
        stop_loss_pct=0.02
    )
    print(decision.get_reasoning_summary())

    print("\n📊 Current Status:")
    status = sizer.get_status()
    for key, value in status.items():
        if isinstance(value, float):
            if value > 100:
                print(f"  {key}: ${value:,.0f}")
            else:
                print(f"  {key}: {value:.2%}")
        else:
            print(f"  {key}: {value}")

    print("\n" + "="*80)
    print("✅ DYNAMIC POSITION SIZING DEMO COMPLETE")
    print("="*80)


if __name__ == "__main__":
    example_usage()
