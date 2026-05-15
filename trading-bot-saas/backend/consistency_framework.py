"""
Trading Consistency Framework
The missing piece that turns good strategies into reliable profits

CRITICAL PROBLEM:
- You generate signals but never track if they're accurate
- You execute trades but don't measure slippage
- You see returns but don't know if they're consistent or lucky

SOLUTION:
- Track every signal's actual outcome
- Measure execution quality
- Monitor performance degradation
- Enforce consistency guardrails

This is NOT nice-to-have. This is SURVIVAL.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import deque
from enum import Enum
import statistics

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# DATA MODELS
# ============================================================================

class SignalOutcome(Enum):
    """Signal outcome after trade closes"""
    WIN = "win"
    LOSS = "loss"
    SCRATCH = "scratch"  # Break-even
    TIMEOUT = "timeout"  # Expired without execution


@dataclass
class SignalPerformanceRecord:
    """
    Tracks actual performance of each signal
    This is what's MISSING - you never validate your signals!
    """
    signal_id: str
    bot_id: int
    symbol: str
    signal_type: str  # BUY, SELL, LONG_SPREAD, etc.

    # Entry
    generated_at: datetime
    entry_price: float
    confidence: float
    expected_return: float  # What you THOUGHT would happen

    # Exit
    closed_at: Optional[datetime] = None
    exit_price: Optional[float] = None
    actual_return: Optional[float] = None  # What ACTUALLY happened
    outcome: Optional[SignalOutcome] = None

    # Execution quality
    entry_slippage: float = 0.0  # Difference between expected and actual entry
    exit_slippage: float = 0.0
    total_fees: float = 0.0

    # Context
    market_regime: str = "unknown"
    volatility_at_entry: float = 0.0

    def calculate_outcome(self) -> SignalOutcome:
        """Determine if signal was accurate"""
        if self.actual_return is None:
            return SignalOutcome.TIMEOUT

        # After fees and slippage
        net_return = self.actual_return - self.total_fees - self.entry_slippage - self.exit_slippage

        if net_return > 0.001:  # >10 bps profit
            return SignalOutcome.WIN
        elif net_return < -0.001:  # >10 bps loss
            return SignalOutcome.LOSS
        else:
            return SignalOutcome.SCRATCH

    def confidence_was_accurate(self) -> bool:
        """Was high confidence actually high profit?"""
        if self.actual_return is None:
            return False

        # High confidence should mean high returns
        if self.confidence > 0.8:
            return self.actual_return > 0.005  # Should make >50 bps
        elif self.confidence > 0.6:
            return self.actual_return > 0.002  # Should make >20 bps
        else:
            return self.actual_return > 0.0  # Just don't lose


@dataclass
class ExecutionQualityMetrics:
    """
    Measures how well trades execute vs expectations
    CRITICAL - Hidden costs kill profits
    """
    trade_id: str
    symbol: str

    # Expected vs actual
    expected_entry_price: float
    actual_entry_price: float
    expected_exit_price: Optional[float] = None
    actual_exit_price: Optional[float] = None

    # Slippage (basis points)
    entry_slippage_bps: float = 0.0
    exit_slippage_bps: Optional[float] = None

    # Fill quality
    intended_size: float = 0.0
    filled_size: float = 0.0
    fill_rate: float = 0.0  # filled / intended
    time_to_fill_seconds: float = 0.0

    # Fees
    expected_fee: float = 0.0
    actual_fee: float = 0.0

    def calculate_implementation_shortfall(self) -> float:
        """
        Total cost of execution vs perfect execution
        This is your HIDDEN COST
        """
        entry_shortfall = (self.actual_entry_price - self.expected_entry_price) / self.expected_entry_price

        if self.actual_exit_price and self.expected_exit_price:
            exit_shortfall = (self.expected_exit_price - self.actual_exit_price) / self.expected_exit_price
        else:
            exit_shortfall = 0.0

        fee_shortfall = self.actual_fee - self.expected_fee

        return (entry_shortfall + exit_shortfall + fee_shortfall) * 10000  # in bps


@dataclass
class RollingPerformanceMetrics:
    """
    Tracks performance over rolling windows
    Detects degradation BEFORE it destroys your account
    """
    window_size: int  # Number of trades

    # Recent trades
    recent_returns: deque
    recent_outcomes: deque
    recent_holding_times: deque

    def __post_init__(self):
        self.recent_returns = deque(maxlen=self.window_size)
        self.recent_outcomes = deque(maxlen=self.window_size)
        self.recent_holding_times = deque(maxlen=self.window_size)

    def add_trade(self, return_pct: float, outcome: SignalOutcome, holding_seconds: float):
        """Add trade to rolling window"""
        self.recent_returns.append(return_pct)
        self.recent_outcomes.append(outcome)
        self.recent_holding_times.append(holding_seconds)

    def get_win_rate(self) -> float:
        """Win rate over window"""
        if not self.recent_outcomes:
            return 0.0

        wins = sum(1 for o in self.recent_outcomes if o == SignalOutcome.WIN)
        return wins / len(self.recent_outcomes)

    def get_avg_return(self) -> float:
        """Average return over window"""
        if not self.recent_returns:
            return 0.0

        return statistics.mean(self.recent_returns)

    def get_sharpe_ratio(self) -> float:
        """Sharpe ratio over window"""
        if len(self.recent_returns) < 2:
            return 0.0

        avg_return = statistics.mean(self.recent_returns)
        std_return = statistics.stdev(self.recent_returns)

        if std_return == 0:
            return 0.0

        # Annualized Sharpe (assuming daily returns)
        return (avg_return / std_return) * (252 ** 0.5)

    def detect_degradation(self, baseline_win_rate: float, threshold: float = 0.15) -> bool:
        """
        Detect if performance degraded significantly

        Args:
            baseline_win_rate: Historical win rate
            threshold: Degradation threshold (e.g., 0.15 = 15% worse)

        Returns:
            True if degraded
        """
        current_win_rate = self.get_win_rate()

        # If win rate dropped more than threshold
        degradation = baseline_win_rate - current_win_rate
        return degradation > threshold


# ============================================================================
# SIGNAL PERFORMANCE TRACKER
# ============================================================================

class SignalPerformanceTracker:
    """
    Tracks every signal's actual outcome
    ANSWERS THE QUESTION: "Are my signals actually good?"
    """

    def __init__(self, database_session=None):
        self.session = database_session

        # In-memory cache
        self.active_signals: Dict[str, SignalPerformanceRecord] = {}
        self.completed_signals: List[SignalPerformanceRecord] = []

        # Performance by category
        self.performance_by_type: Dict[str, RollingPerformanceMetrics] = {}
        self.performance_by_symbol: Dict[str, RollingPerformanceMetrics] = {}
        self.performance_by_confidence: Dict[str, RollingPerformanceMetrics] = {}

        logger.info("✅ Signal Performance Tracker initialized")

    async def track_signal(self, signal: Dict) -> str:
        """
        Start tracking a new signal

        Args:
            signal: Signal data with type, confidence, expected_return

        Returns:
            Signal ID for tracking
        """
        import uuid

        signal_id = signal.get('id', str(uuid.uuid4()))

        record = SignalPerformanceRecord(
            signal_id=signal_id,
            bot_id=signal['bot_id'],
            symbol=signal['symbol'],
            signal_type=signal['type'],
            generated_at=datetime.utcnow(),
            entry_price=signal['price'],
            confidence=signal.get('confidence', 0.0),
            expected_return=signal.get('expected_return', 0.0),
            market_regime=signal.get('market_regime', 'unknown'),
            volatility_at_entry=signal.get('volatility', 0.0)
        )

        self.active_signals[signal_id] = record

        # Save to database
        if self.session:
            await self._save_signal_to_db(record)

        logger.info(f"📊 Tracking signal: {signal_id} ({signal['type']} {signal['symbol']} @ {signal['price']})")

        return signal_id

    async def close_signal(
        self,
        signal_id: str,
        exit_price: float,
        entry_slippage: float = 0.0,
        exit_slippage: float = 0.0,
        total_fees: float = 0.0
    ):
        """
        Close signal and record actual outcome

        This is THE CRITICAL STEP you're missing - validating signals!
        """
        if signal_id not in self.active_signals:
            logger.warning(f"⚠️ Signal {signal_id} not found in active signals")
            return

        record = self.active_signals[signal_id]

        # Update record
        record.closed_at = datetime.utcnow()
        record.exit_price = exit_price
        record.entry_slippage = entry_slippage
        record.exit_slippage = exit_slippage
        record.total_fees = total_fees

        # Calculate actual return
        price_change = (exit_price - record.entry_price) / record.entry_price
        record.actual_return = price_change - total_fees - entry_slippage - exit_slippage

        # Determine outcome
        record.outcome = record.calculate_outcome()

        # Was confidence accurate?
        confidence_accurate = record.confidence_was_accurate()

        # Move to completed
        self.completed_signals.append(record)
        del self.active_signals[signal_id]

        # Update rolling metrics
        await self._update_rolling_metrics(record)

        # Save to database
        if self.session:
            await self._update_signal_in_db(record)

        # Log result
        logger.info(f"📊 Signal closed: {signal_id}")
        logger.info(f"   Outcome: {record.outcome.value}")
        logger.info(f"   Expected: {record.expected_return:.2%}")
        logger.info(f"   Actual: {record.actual_return:.2%}")
        logger.info(f"   Confidence accurate: {confidence_accurate}")

    async def _update_rolling_metrics(self, record: SignalPerformanceRecord):
        """Update rolling performance metrics by category"""

        # Initialize rolling metrics if needed
        if record.signal_type not in self.performance_by_type:
            self.performance_by_type[record.signal_type] = RollingPerformanceMetrics(window_size=50)

        if record.symbol not in self.performance_by_symbol:
            self.performance_by_symbol[record.symbol] = RollingPerformanceMetrics(window_size=30)

        confidence_bucket = self._get_confidence_bucket(record.confidence)
        if confidence_bucket not in self.performance_by_confidence:
            self.performance_by_confidence[confidence_bucket] = RollingPerformanceMetrics(window_size=50)

        # Calculate holding time
        holding_seconds = (record.closed_at - record.generated_at).total_seconds()

        # Update all relevant metrics
        self.performance_by_type[record.signal_type].add_trade(
            record.actual_return, record.outcome, holding_seconds
        )

        self.performance_by_symbol[record.symbol].add_trade(
            record.actual_return, record.outcome, holding_seconds
        )

        self.performance_by_confidence[confidence_bucket].add_trade(
            record.actual_return, record.outcome, holding_seconds
        )

    def _get_confidence_bucket(self, confidence: float) -> str:
        """Bucket confidence for analysis"""
        if confidence >= 0.8:
            return "high"
        elif confidence >= 0.6:
            return "medium"
        else:
            return "low"

    def get_performance_report(self) -> Dict:
        """
        Generate comprehensive performance report
        THISANSWERS: "Are my signals degrading?"
        """
        report = {
            "total_signals": len(self.completed_signals),
            "active_signals": len(self.active_signals),
            "by_type": {},
            "by_symbol": {},
            "by_confidence": {},
            "overall": self._calculate_overall_metrics()
        }

        # Performance by signal type
        for signal_type, metrics in self.performance_by_type.items():
            report["by_type"][signal_type] = {
                "win_rate": metrics.get_win_rate(),
                "avg_return": metrics.get_avg_return(),
                "sharpe_ratio": metrics.get_sharpe_ratio(),
                "sample_size": len(metrics.recent_returns)
            }

        # Performance by symbol
        for symbol, metrics in self.performance_by_symbol.items():
            report["by_symbol"][symbol] = {
                "win_rate": metrics.get_win_rate(),
                "avg_return": metrics.get_avg_return(),
                "sharpe_ratio": metrics.get_sharpe_ratio()
            }

        # Performance by confidence
        for confidence_bucket, metrics in self.performance_by_confidence.items():
            report["by_confidence"][confidence_bucket] = {
                "win_rate": metrics.get_win_rate(),
                "avg_return": metrics.get_avg_return(),
                "sharpe_ratio": metrics.get_sharpe_ratio()
            }

        return report

    def _calculate_overall_metrics(self) -> Dict:
        """Calculate overall performance metrics"""
        if not self.completed_signals:
            return {}

        # All returns
        all_returns = [s.actual_return for s in self.completed_signals if s.actual_return is not None]

        # Win rate
        wins = sum(1 for s in self.completed_signals if s.outcome == SignalOutcome.WIN)
        win_rate = wins / len(self.completed_signals)

        # Average return
        avg_return = statistics.mean(all_returns) if all_returns else 0.0

        # Sharpe ratio
        sharpe = 0.0
        if len(all_returns) > 1:
            std = statistics.stdev(all_returns)
            if std > 0:
                sharpe = (avg_return / std) * (252 ** 0.5)

        # Confidence accuracy
        accurate_confidence = sum(
            1 for s in self.completed_signals
            if s.confidence_was_accurate()
        )
        confidence_accuracy = accurate_confidence / len(self.completed_signals)

        return {
            "win_rate": win_rate,
            "avg_return": avg_return,
            "sharpe_ratio": sharpe,
            "confidence_accuracy": confidence_accuracy,
            "total_trades": len(self.completed_signals)
        }

    def check_for_degradation(self, baseline_win_rate: float = 0.6) -> Dict:
        """
        Check if any category showing performance degradation

        Returns:
            Dictionary of degraded categories
        """
        degraded = {}

        # Check each signal type
        for signal_type, metrics in self.performance_by_type.items():
            if metrics.detect_degradation(baseline_win_rate):
                degraded[f"type_{signal_type}"] = {
                    "current_win_rate": metrics.get_win_rate(),
                    "expected_win_rate": baseline_win_rate,
                    "degradation": baseline_win_rate - metrics.get_win_rate()
                }

        # Check symbols
        for symbol, metrics in self.performance_by_symbol.items():
            if metrics.detect_degradation(baseline_win_rate):
                degraded[f"symbol_{symbol}"] = {
                    "current_win_rate": metrics.get_win_rate(),
                    "expected_win_rate": baseline_win_rate,
                    "degradation": baseline_win_rate - metrics.get_win_rate()
                }

        return degraded

    async def _save_signal_to_db(self, record: SignalPerformanceRecord):
        """Save signal to database (implement based on your DB)"""
        # TODO: Implement database persistence
        pass

    async def _update_signal_in_db(self, record: SignalPerformanceRecord):
        """Update signal in database"""
        # TODO: Implement database update
        pass


# ============================================================================
# EXECUTION QUALITY MONITOR
# ============================================================================

class ExecutionQualityMonitor:
    """
    Measures how well trades execute vs expectations
    ANSWERS: "Are we losing money to slippage?"
    """

    def __init__(self):
        self.executions: List[ExecutionQualityMetrics] = []
        self.slippage_by_symbol: Dict[str, deque] = {}

        logger.info("✅ Execution Quality Monitor initialized")

    async def track_execution(
        self,
        trade_id: str,
        symbol: str,
        expected_entry: float,
        actual_entry: float,
        intended_size: float,
        filled_size: float,
        time_to_fill: float,
        expected_fee: float,
        actual_fee: float
    ) -> ExecutionQualityMetrics:
        """Track execution quality"""

        # Calculate slippage in basis points
        entry_slippage_bps = ((actual_entry - expected_entry) / expected_entry) * 10000

        # Calculate fill rate
        fill_rate = filled_size / intended_size if intended_size > 0 else 0.0

        metrics = ExecutionQualityMetrics(
            trade_id=trade_id,
            symbol=symbol,
            expected_entry_price=expected_entry,
            actual_entry_price=actual_entry,
            entry_slippage_bps=entry_slippage_bps,
            intended_size=intended_size,
            filled_size=filled_size,
            fill_rate=fill_rate,
            time_to_fill_seconds=time_to_fill,
            expected_fee=expected_fee,
            actual_fee=actual_fee
        )

        self.executions.append(metrics)

        # Track slippage by symbol
        if symbol not in self.slippage_by_symbol:
            self.slippage_by_symbol[symbol] = deque(maxlen=100)

        self.slippage_by_symbol[symbol].append(entry_slippage_bps)

        # Log quality
        logger.info(f"📊 Execution quality: {trade_id}")
        logger.info(f"   Slippage: {entry_slippage_bps:.2f} bps")
        logger.info(f"   Fill rate: {fill_rate:.1%}")
        logger.info(f"   Time to fill: {time_to_fill:.2f}s")

        # Alert if poor quality
        if entry_slippage_bps > 20:  # >20 bps slippage
            logger.warning(f"⚠️ HIGH SLIPPAGE: {entry_slippage_bps:.2f} bps on {symbol}")

        if fill_rate < 0.95:  # <95% fill rate
            logger.warning(f"⚠️ PARTIAL FILL: Only {fill_rate:.1%} filled on {symbol}")

        return metrics

    def get_average_slippage(self, symbol: Optional[str] = None) -> float:
        """Get average slippage (basis points)"""
        if symbol and symbol in self.slippage_by_symbol:
            slippages = self.slippage_by_symbol[symbol]
        else:
            slippages = [e.entry_slippage_bps for e in self.executions]

        return statistics.mean(slippages) if slippages else 0.0

    def get_execution_report(self) -> Dict:
        """Generate execution quality report"""
        if not self.executions:
            return {}

        all_slippages = [e.entry_slippage_bps for e in self.executions]
        all_fill_rates = [e.fill_rate for e in self.executions]
        all_times = [e.time_to_fill_seconds for e in self.executions]

        return {
            "total_executions": len(self.executions),
            "avg_slippage_bps": statistics.mean(all_slippages),
            "max_slippage_bps": max(all_slippages),
            "avg_fill_rate": statistics.mean(all_fill_rates),
            "avg_time_to_fill": statistics.mean(all_times),
            "by_symbol": {
                symbol: {
                    "avg_slippage_bps": statistics.mean(slippages),
                    "count": len(slippages)
                }
                for symbol, slippages in self.slippage_by_symbol.items()
            }
        }


# ============================================================================
# CONSISTENCY GUARDIAN (Main Orchestrator)
# ============================================================================

class ConsistencyGuardian:
    """
    Orchestrates all consistency monitoring
    THE MISSING PIECE that makes trading reliable
    """

    def __init__(self, database_session=None):
        self.signal_tracker = SignalPerformanceTracker(database_session)
        self.execution_monitor = ExecutionQualityMonitor()

        # Baseline metrics (from backtesting)
        self.baseline_win_rate = 0.6  # 60% win rate expected
        self.baseline_sharpe = 1.0  # Sharpe ratio 1.0 expected

        logger.info("=" * 80)
        logger.info("CONSISTENCY GUARDIAN INITIALIZED")
        logger.info("=" * 80)
        logger.info("✅ Signal Performance Tracker")
        logger.info("✅ Execution Quality Monitor")
        logger.info("=" * 80)

    async def start_signal_tracking(self, signal: Dict) -> str:
        """Start tracking a new signal"""
        return await self.signal_tracker.track_signal(signal)

    async def close_signal_tracking(
        self,
        signal_id: str,
        exit_price: float,
        entry_slippage: float = 0.0,
        exit_slippage: float = 0.0,
        total_fees: float = 0.0
    ):
        """Close signal and validate performance"""
        await self.signal_tracker.close_signal(
            signal_id, exit_price,
            entry_slippage, exit_slippage, total_fees
        )

    async def track_execution(self, **kwargs) -> ExecutionQualityMetrics:
        """Track execution quality"""
        return await self.execution_monitor.track_execution(**kwargs)

    def get_health_report(self) -> Dict:
        """
        Get complete consistency health report
        ANSWER: "Is my system reliable?"
        """
        signal_report = self.signal_tracker.get_performance_report()
        execution_report = self.execution_monitor.get_execution_report()
        degradation = self.signal_tracker.check_for_degradation(self.baseline_win_rate)

        return {
            "signal_performance": signal_report,
            "execution_quality": execution_report,
            "degradation_alerts": degradation,
            "timestamp": datetime.utcnow().isoformat()
        }

    def is_system_healthy(self) -> Tuple[bool, List[str]]:
        """
        Check if system is healthy

        Returns:
            (is_healthy, list_of_issues)
        """
        issues = []

        # Check for degradation
        degradation = self.signal_tracker.check_for_degradation(self.baseline_win_rate)
        if degradation:
            for category, data in degradation.items():
                issues.append(
                    f"{category} degraded: {data['current_win_rate']:.1%} "
                    f"vs expected {data['expected_win_rate']:.1%}"
                )

        # Check execution quality
        avg_slippage = self.execution_monitor.get_average_slippage()
        if avg_slippage > 15:  # >15 bps average slippage
            issues.append(f"High average slippage: {avg_slippage:.2f} bps")

        # Check if enough data
        if len(self.signal_tracker.completed_signals) < 10:
            issues.append("Insufficient data for reliability assessment")

        return len(issues) == 0, issues


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

async def example_usage():
    print("\n" + "="*80)
    print("CONSISTENCY FRAMEWORK - DEMO")
    print("="*80)

    # Initialize guardian
    guardian = ConsistencyGuardian()

    # Simulate signal lifecycle
    print("\n📊 Tracking signal lifecycle...")

    # 1. New signal generated
    signal = {
        'id': 'sig_001',
        'bot_id': 1,
        'symbol': 'BTC/USDT',
        'type': 'BUY',
        'price': 50000.0,
        'confidence': 0.85,
        'expected_return': 0.02,  # Expect 2% return
        'market_regime': 'bullish',
        'volatility': 0.015
    }

    signal_id = await guardian.start_signal_tracking(signal)
    print(f"✅ Signal tracked: {signal_id}")

    # 2. Trade executed
    await guardian.track_execution(
        trade_id='trade_001',
        symbol='BTC/USDT',
        expected_entry=50000.0,
        actual_entry=50010.0,  # 10 bps slippage
        intended_size=0.1,
        filled_size=0.1,
        time_to_fill=0.5,
        expected_fee=5.0,
        actual_fee=5.2
    )

    # 3. Signal closes
    await asyncio.sleep(1)  # Simulate holding

    await guardian.close_signal_tracking(
        signal_id=signal_id,
        exit_price=51000.0,  # 2% gain as expected
        entry_slippage=0.0001,  # 1 bp
        exit_slippage=0.0001,  # 1 bp
        total_fees=0.0002  # 2 bps
    )

    # Get health report
    print("\n📊 System Health Report:")
    report = guardian.get_health_report()

    print(f"\n  Overall Metrics:")
    if report['signal_performance'].get('overall'):
        overall = report['signal_performance']['overall']
        print(f"    Win Rate: {overall['win_rate']:.1%}")
        print(f"    Avg Return: {overall['avg_return']:.2%}")
        print(f"    Confidence Accuracy: {overall['confidence_accuracy']:.1%}")

    if report['execution_quality']:
        print(f"\n  Execution Quality:")
        print(f"    Avg Slippage: {report['execution_quality']['avg_slippage_bps']:.2f} bps")
        print(f"    Avg Fill Rate: {report['execution_quality']['avg_fill_rate']:.1%}")

    # Check health
    is_healthy, issues = guardian.is_system_healthy()
    print(f"\n  System Health: {'✅ HEALTHY' if is_healthy else '⚠️ ISSUES DETECTED'}")
    if issues:
        for issue in issues:
            print(f"    - {issue}")

    print("\n" + "="*80)
    print("✅ CONSISTENCY FRAMEWORK READY")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(example_usage())
