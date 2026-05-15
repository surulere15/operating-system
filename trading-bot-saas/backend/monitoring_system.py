"""
Monitoring and Observability System
Production-grade monitoring, metrics, and alerting

Features:
- Error tracking (Sentry integration)
- Performance metrics (Prometheus)
- Health checks
- System monitoring
- Custom alerts
- Performance profiling

Goal: Full system observability in production
"""

import time
import psutil
import logging
from typing import Dict, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import deque, defaultdict
from enum import Enum
import traceback
import json

# Optional dependencies
try:
    import sentry_sdk
    from sentry_sdk import capture_exception, capture_message
    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS
# ============================================================================

class MetricType(Enum):
    """Metric type"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class HealthStatus(Enum):
    """Health check status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class Metric:
    """Performance metric"""
    name: str
    value: float
    metric_type: MetricType
    labels: Dict[str, str]
    timestamp: datetime


@dataclass
class HealthCheck:
    """Health check result"""
    component: str
    status: HealthStatus
    message: str
    response_time_ms: float
    timestamp: datetime
    details: Optional[Dict] = None


@dataclass
class Alert:
    """System alert"""
    severity: AlertSeverity
    title: str
    message: str
    component: str
    timestamp: datetime
    details: Optional[Dict] = None


@dataclass
class PerformanceProfile:
    """Performance profile"""
    operation: str
    duration_ms: float
    cpu_percent: float
    memory_mb: float
    timestamp: datetime
    metadata: Optional[Dict] = None


# ============================================================================
# ERROR TRACKING (SENTRY)
# ============================================================================

class ErrorTracker:
    """
    Error tracking with Sentry integration
    """

    def __init__(self, sentry_dsn: Optional[str] = None, environment: str = "production"):
        """
        Initialize error tracker

        Args:
            sentry_dsn: Sentry DSN URL
            environment: Environment name
        """
        self.sentry_enabled = False

        if sentry_dsn and SENTRY_AVAILABLE:
            sentry_sdk.init(
                dsn=sentry_dsn,
                environment=environment,
                traces_sample_rate=0.1,  # 10% of transactions
                profiles_sample_rate=0.1,  # 10% profiling
            )
            self.sentry_enabled = True
            logger.info("✅ Sentry error tracking initialized")
        else:
            logger.warning("⚠️ Sentry not available - using local error logging")

    def capture_exception(self, exception: Exception, context: Dict = None):
        """
        Capture exception

        Args:
            exception: Exception to capture
            context: Additional context
        """
        if self.sentry_enabled:
            with sentry_sdk.push_scope() as scope:
                if context:
                    for key, value in context.items():
                        scope.set_context(key, value)
                capture_exception(exception)

        # Always log locally
        logger.error(f"Exception captured: {str(exception)}", exc_info=True)

        if context:
            logger.error(f"Context: {json.dumps(context, indent=2)}")

    def capture_message(self, message: str, level: str = "info", context: Dict = None):
        """
        Capture message

        Args:
            message: Message to capture
            level: Log level
            context: Additional context
        """
        if self.sentry_enabled:
            with sentry_sdk.push_scope() as scope:
                if context:
                    for key, value in context.items():
                        scope.set_context(key, value)
                capture_message(message, level=level)

        # Log locally
        log_func = getattr(logger, level.lower(), logger.info)
        log_func(message)

    def set_user_context(self, user_id: str, username: str = None, email: str = None):
        """Set user context for error tracking"""
        if self.sentry_enabled:
            sentry_sdk.set_user({
                "id": user_id,
                "username": username,
                "email": email
            })

    def set_tag(self, key: str, value: str):
        """Set custom tag"""
        if self.sentry_enabled:
            sentry_sdk.set_tag(key, value)


# ============================================================================
# METRICS COLLECTOR
# ============================================================================

class MetricsCollector:
    """
    Collect and aggregate performance metrics
    Prometheus-compatible format
    """

    def __init__(self, retention_minutes: int = 60):
        """
        Initialize metrics collector

        Args:
            retention_minutes: How long to retain metrics
        """
        self.retention_minutes = retention_minutes
        self.retention_seconds = retention_minutes * 60

        # Metrics storage
        self.counters: Dict[str, float] = defaultdict(float)
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))

        # Time series data
        self.time_series: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))

        logger.info(f"✅ Metrics collector initialized (retention: {retention_minutes}m)")

    def increment_counter(self, name: str, value: float = 1.0, labels: Dict[str, str] = None):
        """
        Increment counter metric

        Args:
            name: Metric name
            value: Increment value
            labels: Metric labels
        """
        key = self._make_key(name, labels)
        self.counters[key] += value

        # Store time series
        self.time_series[key].append(Metric(
            name=name,
            value=self.counters[key],
            metric_type=MetricType.COUNTER,
            labels=labels or {},
            timestamp=datetime.utcnow()
        ))

    def set_gauge(self, name: str, value: float, labels: Dict[str, str] = None):
        """
        Set gauge metric

        Args:
            name: Metric name
            value: Gauge value
            labels: Metric labels
        """
        key = self._make_key(name, labels)
        self.gauges[key] = value

        # Store time series
        self.time_series[key].append(Metric(
            name=name,
            value=value,
            metric_type=MetricType.GAUGE,
            labels=labels or {},
            timestamp=datetime.utcnow()
        ))

    def observe_histogram(self, name: str, value: float, labels: Dict[str, str] = None):
        """
        Observe histogram value

        Args:
            name: Metric name
            value: Observed value
            labels: Metric labels
        """
        key = self._make_key(name, labels)
        self.histograms[key].append(value)

        # Store time series
        self.time_series[key].append(Metric(
            name=name,
            value=value,
            metric_type=MetricType.HISTOGRAM,
            labels=labels or {},
            timestamp=datetime.utcnow()
        ))

    def get_counter(self, name: str, labels: Dict[str, str] = None) -> float:
        """Get counter value"""
        key = self._make_key(name, labels)
        return self.counters.get(key, 0.0)

    def get_gauge(self, name: str, labels: Dict[str, str] = None) -> float:
        """Get gauge value"""
        key = self._make_key(name, labels)
        return self.gauges.get(key, 0.0)

    def get_histogram_stats(self, name: str, labels: Dict[str, str] = None) -> Dict:
        """Get histogram statistics"""
        key = self._make_key(name, labels)
        values = list(self.histograms.get(key, []))

        if not values:
            return {"count": 0}

        values_sorted = sorted(values)
        count = len(values)

        return {
            "count": count,
            "sum": sum(values),
            "avg": sum(values) / count,
            "min": min(values),
            "max": max(values),
            "p50": values_sorted[int(count * 0.5)],
            "p95": values_sorted[int(count * 0.95)],
            "p99": values_sorted[int(count * 0.99)],
        }

    def get_all_metrics(self) -> Dict[str, any]:
        """Get all metrics"""
        return {
            "counters": dict(self.counters),
            "gauges": dict(self.gauges),
            "histograms": {
                name: self.get_histogram_stats(name)
                for name in self.histograms.keys()
            }
        }

    def _make_key(self, name: str, labels: Dict[str, str] = None) -> str:
        """Make metric key from name and labels"""
        if not labels:
            return name

        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"

    def cleanup_old_metrics(self):
        """Remove metrics older than retention period"""
        cutoff = datetime.utcnow() - timedelta(seconds=self.retention_seconds)

        for name, metrics in self.time_series.items():
            while metrics and metrics[0].timestamp < cutoff:
                metrics.popleft()


# ============================================================================
# HEALTH CHECKER
# ============================================================================

class HealthChecker:
    """
    System health monitoring
    """

    def __init__(self):
        """Initialize health checker"""
        self.health_checks: Dict[str, HealthCheck] = {}
        self.check_functions: Dict[str, Callable] = {}

        logger.info("✅ Health checker initialized")

    def register_check(self, component: str, check_func: Callable):
        """
        Register health check function

        Args:
            component: Component name
            check_func: Health check function (should return bool and message)
        """
        self.check_functions[component] = check_func
        logger.info(f"✅ Registered health check for: {component}")

    async def check_component(self, component: str) -> HealthCheck:
        """
        Check component health

        Args:
            component: Component name

        Returns:
            Health check result
        """
        if component not in self.check_functions:
            return HealthCheck(
                component=component,
                status=HealthStatus.UNHEALTHY,
                message="No health check registered",
                response_time_ms=0,
                timestamp=datetime.utcnow()
            )

        start_time = time.time()

        try:
            check_func = self.check_functions[component]
            is_healthy, message, details = await check_func()

            response_time_ms = (time.time() - start_time) * 1000

            status = HealthStatus.HEALTHY if is_healthy else HealthStatus.UNHEALTHY

            health_check = HealthCheck(
                component=component,
                status=status,
                message=message,
                response_time_ms=response_time_ms,
                timestamp=datetime.utcnow(),
                details=details
            )

            self.health_checks[component] = health_check
            return health_check

        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000

            health_check = HealthCheck(
                component=component,
                status=HealthStatus.UNHEALTHY,
                message=f"Health check failed: {str(e)}",
                response_time_ms=response_time_ms,
                timestamp=datetime.utcnow(),
                details={"error": str(e), "traceback": traceback.format_exc()}
            )

            self.health_checks[component] = health_check
            return health_check

    async def check_all(self) -> Dict[str, HealthCheck]:
        """Check all components"""
        results = {}

        for component in self.check_functions.keys():
            results[component] = await self.check_component(component)

        return results

    def get_overall_status(self) -> HealthStatus:
        """Get overall system health status"""
        if not self.health_checks:
            return HealthStatus.UNHEALTHY

        statuses = [check.status for check in self.health_checks.values()]

        if all(status == HealthStatus.HEALTHY for status in statuses):
            return HealthStatus.HEALTHY
        elif any(status == HealthStatus.UNHEALTHY for status in statuses):
            return HealthStatus.UNHEALTHY
        else:
            return HealthStatus.DEGRADED


# ============================================================================
# SYSTEM MONITOR
# ============================================================================

class SystemMonitor:
    """
    Monitor system resources
    """

    def __init__(self):
        """Initialize system monitor"""
        self.process = psutil.Process()
        logger.info("✅ System monitor initialized")

    def get_cpu_usage(self) -> float:
        """Get CPU usage percentage"""
        return self.process.cpu_percent(interval=0.1)

    def get_memory_usage(self) -> Dict:
        """Get memory usage"""
        mem = self.process.memory_info()
        return {
            "rss_mb": mem.rss / 1024 / 1024,  # Resident Set Size
            "vms_mb": mem.vms / 1024 / 1024,  # Virtual Memory Size
            "percent": self.process.memory_percent()
        }

    def get_disk_usage(self) -> Dict:
        """Get disk usage"""
        disk = psutil.disk_usage('/')
        return {
            "total_gb": disk.total / 1024 / 1024 / 1024,
            "used_gb": disk.used / 1024 / 1024 / 1024,
            "free_gb": disk.free / 1024 / 1024 / 1024,
            "percent": disk.percent
        }

    def get_network_stats(self) -> Dict:
        """Get network statistics"""
        net = psutil.net_io_counters()
        return {
            "bytes_sent": net.bytes_sent,
            "bytes_recv": net.bytes_recv,
            "packets_sent": net.packets_sent,
            "packets_recv": net.packets_recv
        }

    def get_all_stats(self) -> Dict:
        """Get all system statistics"""
        return {
            "cpu": {
                "process_percent": self.get_cpu_usage(),
                "system_percent": psutil.cpu_percent(interval=0.1),
                "count": psutil.cpu_count()
            },
            "memory": self.get_memory_usage(),
            "disk": self.get_disk_usage(),
            "network": self.get_network_stats(),
            "timestamp": datetime.utcnow().isoformat()
        }


# ============================================================================
# ALERT MANAGER
# ============================================================================

class AlertManager:
    """
    Alert management and notification
    """

    def __init__(self, metrics_collector: MetricsCollector):
        """
        Initialize alert manager

        Args:
            metrics_collector: Metrics collector instance
        """
        self.metrics = metrics_collector
        self.alerts: deque = deque(maxlen=1000)

        # Alert thresholds
        self.thresholds = {
            "error_rate": 0.05,  # 5% error rate
            "response_time_ms": 1000,  # 1 second
            "cpu_percent": 80,  # 80% CPU
            "memory_percent": 85,  # 85% memory
            "disk_percent": 90,  # 90% disk
        }

        logger.info("✅ Alert manager initialized")

    def create_alert(self, severity: AlertSeverity, title: str, message: str,
                    component: str, details: Dict = None):
        """
        Create alert

        Args:
            severity: Alert severity
            title: Alert title
            message: Alert message
            component: Component name
            details: Additional details
        """
        alert = Alert(
            severity=severity,
            title=title,
            message=message,
            component=component,
            timestamp=datetime.utcnow(),
            details=details
        )

        self.alerts.append(alert)

        # Increment alert counter
        self.metrics.increment_counter(
            "alerts_total",
            labels={"severity": severity.value, "component": component}
        )

        # Log alert
        log_func = {
            AlertSeverity.INFO: logger.info,
            AlertSeverity.WARNING: logger.warning,
            AlertSeverity.ERROR: logger.error,
            AlertSeverity.CRITICAL: logger.critical
        }.get(severity, logger.info)

        log_func(f"🚨 ALERT [{severity.value.upper()}] {title}: {message}")

        return alert

    def check_thresholds(self, system_monitor: SystemMonitor):
        """Check system thresholds and create alerts"""
        stats = system_monitor.get_all_stats()

        # Check CPU
        if stats['cpu']['process_percent'] > self.thresholds['cpu_percent']:
            self.create_alert(
                AlertSeverity.WARNING,
                "High CPU Usage",
                f"CPU usage at {stats['cpu']['process_percent']:.1f}%",
                "system",
                {"cpu_stats": stats['cpu']}
            )

        # Check memory
        if stats['memory']['percent'] > self.thresholds['memory_percent']:
            self.create_alert(
                AlertSeverity.WARNING,
                "High Memory Usage",
                f"Memory usage at {stats['memory']['percent']:.1f}%",
                "system",
                {"memory_stats": stats['memory']}
            )

        # Check disk
        if stats['disk']['percent'] > self.thresholds['disk_percent']:
            self.create_alert(
                AlertSeverity.CRITICAL,
                "High Disk Usage",
                f"Disk usage at {stats['disk']['percent']:.1f}%",
                "system",
                {"disk_stats": stats['disk']}
            )

    def get_recent_alerts(self, minutes: int = 60, severity: AlertSeverity = None) -> List[Alert]:
        """Get recent alerts"""
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)

        alerts = [
            alert for alert in self.alerts
            if alert.timestamp >= cutoff
        ]

        if severity:
            alerts = [alert for alert in alerts if alert.severity == severity]

        return alerts


# ============================================================================
# PERFORMANCE PROFILER
# ============================================================================

class PerformanceProfiler:
    """
    Profile code performance
    """

    def __init__(self, metrics_collector: MetricsCollector):
        """
        Initialize profiler

        Args:
            metrics_collector: Metrics collector instance
        """
        self.metrics = metrics_collector
        self.profiles: deque = deque(maxlen=1000)
        self.system_monitor = SystemMonitor()

        logger.info("✅ Performance profiler initialized")

    def profile(self, operation: str):
        """
        Context manager for profiling

        Usage:
            with profiler.profile("my_operation"):
                # Code to profile
                pass
        """
        return ProfileContext(self, operation)

    def record_profile(self, profile: PerformanceProfile):
        """Record performance profile"""
        self.profiles.append(profile)

        # Record metrics
        self.metrics.observe_histogram(
            "operation_duration_ms",
            profile.duration_ms,
            labels={"operation": profile.operation}
        )

        self.metrics.observe_histogram(
            "operation_cpu_percent",
            profile.cpu_percent,
            labels={"operation": profile.operation}
        )

        self.metrics.observe_histogram(
            "operation_memory_mb",
            profile.memory_mb,
            labels={"operation": profile.operation}
        )

    def get_operation_stats(self, operation: str) -> Dict:
        """Get statistics for operation"""
        operation_profiles = [p for p in self.profiles if p.operation == operation]

        if not operation_profiles:
            return {"count": 0}

        durations = [p.duration_ms for p in operation_profiles]
        cpu = [p.cpu_percent for p in operation_profiles]
        memory = [p.memory_mb for p in operation_profiles]

        return {
            "count": len(operation_profiles),
            "duration_ms": {
                "avg": sum(durations) / len(durations),
                "min": min(durations),
                "max": max(durations),
                "p95": sorted(durations)[int(len(durations) * 0.95)]
            },
            "cpu_percent": {
                "avg": sum(cpu) / len(cpu),
                "max": max(cpu)
            },
            "memory_mb": {
                "avg": sum(memory) / len(memory),
                "max": max(memory)
            }
        }


class ProfileContext:
    """Context manager for profiling"""

    def __init__(self, profiler: PerformanceProfiler, operation: str):
        self.profiler = profiler
        self.operation = operation
        self.start_time = None
        self.start_cpu = None
        self.start_memory = None

    def __enter__(self):
        self.start_time = time.time()
        self.start_cpu = self.profiler.system_monitor.get_cpu_usage()
        self.start_memory = self.profiler.system_monitor.get_memory_usage()['rss_mb']
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (time.time() - self.start_time) * 1000
        end_cpu = self.profiler.system_monitor.get_cpu_usage()
        end_memory = self.profiler.system_monitor.get_memory_usage()['rss_mb']

        profile = PerformanceProfile(
            operation=self.operation,
            duration_ms=duration_ms,
            cpu_percent=(self.start_cpu + end_cpu) / 2,
            memory_mb=end_memory - self.start_memory,
            timestamp=datetime.utcnow()
        )

        self.profiler.record_profile(profile)


# ============================================================================
# MONITORING COORDINATOR
# ============================================================================

class MonitoringSystem:
    """
    Complete monitoring system
    """

    def __init__(self, sentry_dsn: Optional[str] = None, environment: str = "production"):
        """
        Initialize monitoring system

        Args:
            sentry_dsn: Sentry DSN
            environment: Environment name
        """
        self.error_tracker = ErrorTracker(sentry_dsn, environment)
        self.metrics = MetricsCollector()
        self.health_checker = HealthChecker()
        self.system_monitor = SystemMonitor()
        self.alert_manager = AlertManager(self.metrics)
        self.profiler = PerformanceProfiler(self.metrics)

        logger.info("✅ Monitoring system initialized")

    def get_system_status(self) -> Dict:
        """Get comprehensive system status"""
        return {
            "health": {
                "overall": self.health_checker.get_overall_status().value,
                "components": {
                    name: asdict(check)
                    for name, check in self.health_checker.health_checks.items()
                }
            },
            "system": self.system_monitor.get_all_stats(),
            "metrics": self.metrics.get_all_metrics(),
            "alerts": {
                "total": len(self.alert_manager.alerts),
                "recent": [asdict(alert) for alert in self.alert_manager.get_recent_alerts(minutes=5)]
            }
        }


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    import asyncio

    async def example_monitoring():
        print("\n" + "="*80)
        print("MONITORING SYSTEM - DEMO")
        print("="*80)

        # Initialize monitoring
        monitoring = MonitoringSystem(environment="development")

        # Record metrics
        print("\n📊 Recording metrics...")
        monitoring.metrics.increment_counter("trades_total", labels={"status": "filled"})
        monitoring.metrics.set_gauge("open_positions", 5)
        monitoring.metrics.observe_histogram("trade_latency_ms", 123.45)

        # Profile operation
        print("\n⚡ Profiling operation...")
        with monitoring.profiler.profile("example_operation"):
            time.sleep(0.1)  # Simulate work

        # Register health check
        async def database_health_check():
            return True, "Database connected", {"latency_ms": 15}

        monitoring.health_checker.register_check("database", database_health_check)

        # Check health
        print("\n🏥 Checking health...")
        health = await monitoring.health_checker.check_all()
        for component, check in health.items():
            print(f"  {component}: {check.status.value} - {check.message}")

        # System stats
        print("\n💻 System stats:")
        stats = monitoring.system_monitor.get_all_stats()
        print(f"  CPU: {stats['cpu']['process_percent']:.1f}%")
        print(f"  Memory: {stats['memory']['rss_mb']:.1f} MB")

        # Get full status
        print("\n📈 Full system status:")
        status = monitoring.get_system_status()
        print(json.dumps(status, indent=2, default=str))

        print("\n✅ Monitoring demo complete")

    asyncio.run(example_monitoring())
