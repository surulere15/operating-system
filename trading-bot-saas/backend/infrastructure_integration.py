"""
Infrastructure Integration Layer
Wires together all production infrastructure components

Components:
- Database operations and ORM
- Production infrastructure (error handling, rate limiting, circuit breakers)
- Monitoring and observability
- Secure key storage
- Position tracking

Usage:
    from infrastructure_integration import get_infrastructure

    infra = get_infrastructure()

    # Use integrated components
    async with infra.database.get_session() as session:
        user = await infra.repos.users.get_user_by_id(user_id)

    # Execute with production safeguards
    result = await infra.production.execute_safe(my_function)

    # Record metrics
    infra.monitoring.metrics.increment_counter("api_calls_total")
"""

import os
from typing import Optional
from contextlib import asynccontextmanager

from database_schema import DatabaseManager
from database_operations import TradingRepository
from production_infrastructure import ProductionInfrastructure
from monitoring_system import MonitoringSystem


# ============================================================================
# CONFIGURATION
# ============================================================================

class InfrastructureConfig:
    """Infrastructure configuration from environment variables"""

    def __init__(self):
        # Database
        self.DATABASE_URL = os.getenv(
            "DATABASE_URL",
            "sqlite:///./trading_bot.db"
        )
        self.DATABASE_ECHO = os.getenv("DATABASE_ECHO", "false").lower() == "true"

        # Sentry
        self.SENTRY_DSN = os.getenv("SENTRY_DSN", None)
        self.ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

        # Rate Limiting
        self.RATE_LIMIT_PER_SECOND = int(os.getenv("RATE_LIMIT_PER_SECOND", "10"))
        self.RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "100"))
        self.RATE_LIMIT_PER_HOUR = int(os.getenv("RATE_LIMIT_PER_HOUR", "1000"))
        self.RATE_LIMIT_PER_DAY = int(os.getenv("RATE_LIMIT_PER_DAY", "10000"))

        # Circuit Breaker
        self.CIRCUIT_BREAKER_FAILURE_THRESHOLD = int(os.getenv("CIRCUIT_BREAKER_FAILURE_THRESHOLD", "5"))
        self.CIRCUIT_BREAKER_RECOVERY_TIMEOUT = int(os.getenv("CIRCUIT_BREAKER_RECOVERY_TIMEOUT", "60"))

        # Security
        self.ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", None)
        if not self.ENCRYPTION_KEY:
            # Generate encryption key for development
            from cryptography.fernet import Fernet
            self.ENCRYPTION_KEY = Fernet.generate_key().decode()
            print(f"⚠️ Generated temporary encryption key (set ENCRYPTION_KEY env var for production)")

        # Retry Configuration
        self.MAX_RETRY_ATTEMPTS = int(os.getenv("MAX_RETRY_ATTEMPTS", "3"))
        self.RETRY_BASE_DELAY = float(os.getenv("RETRY_BASE_DELAY", "1.0"))
        self.RETRY_MAX_DELAY = float(os.getenv("RETRY_MAX_DELAY", "60.0"))


# ============================================================================
# INTEGRATED INFRASTRUCTURE
# ============================================================================

class IntegratedInfrastructure:
    """
    Complete production infrastructure
    All components wired together and ready to use
    """

    def __init__(self, config: InfrastructureConfig = None):
        """
        Initialize infrastructure

        Args:
            config: Infrastructure configuration
        """
        self.config = config or InfrastructureConfig()

        # Initialize components
        print("\n" + "="*80)
        print("INITIALIZING PRODUCTION INFRASTRUCTURE")
        print("="*80)

        # 1. Database
        print("\n1️⃣ Initializing database...")
        self.database = DatabaseManager(
            database_url=self.config.DATABASE_URL,
            echo=self.config.DATABASE_ECHO
        )
        print(f"   ✅ Database: {self.config.DATABASE_URL}")

        # 2. Monitoring
        print("\n2️⃣ Initializing monitoring...")
        self.monitoring = MonitoringSystem(
            sentry_dsn=self.config.SENTRY_DSN,
            environment=self.config.ENVIRONMENT
        )
        print(f"   ✅ Environment: {self.config.ENVIRONMENT}")
        if self.config.SENTRY_DSN:
            print(f"   ✅ Sentry: Enabled")
        else:
            print(f"   ⚠️ Sentry: Disabled (set SENTRY_DSN)")

        # 3. Production Infrastructure
        print("\n3️⃣ Initializing production infrastructure...")
        self.production = ProductionInfrastructure(
            encryption_key=self.config.ENCRYPTION_KEY,
            rate_limit_config={
                "per_second": self.config.RATE_LIMIT_PER_SECOND,
                "per_minute": self.config.RATE_LIMIT_PER_MINUTE,
                "per_hour": self.config.RATE_LIMIT_PER_HOUR,
                "per_day": self.config.RATE_LIMIT_PER_DAY,
            },
            circuit_breaker_config={
                "failure_threshold": self.config.CIRCUIT_BREAKER_FAILURE_THRESHOLD,
                "recovery_timeout": self.config.CIRCUIT_BREAKER_RECOVERY_TIMEOUT,
            }
        )
        print(f"   ✅ Error handling: Retry with exponential backoff")
        print(f"   ✅ Rate limiting: {self.config.RATE_LIMIT_PER_SECOND}/s, {self.config.RATE_LIMIT_PER_MINUTE}/m")
        print(f"   ✅ Circuit breaker: Threshold {self.config.CIRCUIT_BREAKER_FAILURE_THRESHOLD}")
        print(f"   ✅ Encryption: Enabled")

        # 4. Register health checks
        print("\n4️⃣ Registering health checks...")
        self._register_health_checks()
        print(f"   ✅ Health checks: {len(self.monitoring.health_checker.check_functions)} registered")

        print("\n" + "="*80)
        print("✅ INFRASTRUCTURE READY")
        print("="*80 + "\n")

    def get_repository(self) -> TradingRepository:
        """
        Get database repository with new session

        Returns:
            TradingRepository instance
        """
        session = self.database.get_session()
        return TradingRepository(session)

    @asynccontextmanager
    async def get_repository_context(self):
        """
        Get database repository as async context manager
        Automatically handles session cleanup

        Usage:
            async with infra.get_repository_context() as repo:
                user = repo.users.get_user_by_id(1)
        """
        repo = self.get_repository()
        try:
            yield repo
            repo.commit()
        except Exception as e:
            repo.rollback()
            self.monitoring.error_tracker.capture_exception(e)
            raise
        finally:
            repo.close()

    def _register_health_checks(self):
        """Register health checks for all components"""

        # Database health check
        async def database_health_check():
            try:
                # Try to execute simple query
                repo = self.get_repository()
                try:
                    # Just check if session is working
                    repo.session.execute("SELECT 1")
                    repo.close()
                    return True, "Database connected", {"status": "ok"}
                except Exception as e:
                    repo.close()
                    return False, f"Database error: {str(e)}", {"error": str(e)}
            except Exception as e:
                return False, f"Database connection failed: {str(e)}", {"error": str(e)}

        self.monitoring.health_checker.register_check("database", database_health_check)

        # Rate limiter health check
        async def rate_limiter_health_check():
            try:
                status = self.production.rate_limiter.get_status()
                return True, "Rate limiter operational", status
            except Exception as e:
                return False, f"Rate limiter error: {str(e)}", {"error": str(e)}

        self.monitoring.health_checker.register_check("rate_limiter", rate_limiter_health_check)

        # Circuit breaker health check
        async def circuit_breaker_health_check():
            try:
                status = self.production.circuit_breaker.get_status()
                is_healthy = status['state'] != 'OPEN'
                message = f"Circuit breaker: {status['state']}"
                return is_healthy, message, status
            except Exception as e:
                return False, f"Circuit breaker error: {str(e)}", {"error": str(e)}

        self.monitoring.health_checker.register_check("circuit_breaker", circuit_breaker_health_check)

        # Key vault health check
        async def key_vault_health_check():
            try:
                # Test encryption/decryption
                test_data = "test_api_key"
                encrypted = self.production.key_vault.store_api_key("test_health_check", test_data, "test_secret")
                decrypted = self.production.key_vault.retrieve_api_key("test_health_check")

                if decrypted and decrypted['api_key'] == test_data:
                    # Cleanup test key
                    self.production.key_vault.delete_api_key("test_health_check")
                    return True, "Key vault operational", {"status": "ok"}
                else:
                    return False, "Key vault encryption/decryption failed", {"status": "error"}
            except Exception as e:
                return False, f"Key vault error: {str(e)}", {"error": str(e)}

        self.monitoring.health_checker.register_check("key_vault", key_vault_health_check)

    async def get_health_status(self):
        """Get complete health status"""
        health_checks = await self.monitoring.health_checker.check_all()
        overall_status = self.monitoring.health_checker.get_overall_status()

        return {
            "status": overall_status.value,
            "components": {
                name: {
                    "status": check.status.value,
                    "message": check.message,
                    "response_time_ms": check.response_time_ms,
                    "details": check.details
                }
                for name, check in health_checks.items()
            },
            "timestamp": self.monitoring.system_monitor.get_all_stats()["timestamp"]
        }

    def get_system_metrics(self):
        """Get all system metrics"""
        return {
            "infrastructure": {
                "rate_limiter": self.production.rate_limiter.get_status(),
                "circuit_breaker": self.production.circuit_breaker.get_status(),
                "position_tracker": {
                    "open_positions": len(self.production.position_tracker.positions),
                    "total_capital_in_use": sum(
                        p.size * p.entry_price
                        for p in self.production.position_tracker.positions.values()
                    )
                }
            },
            "monitoring": self.monitoring.metrics.get_all_metrics(),
            "system": self.monitoring.system_monitor.get_all_stats()
        }


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

_infrastructure_instance: Optional[IntegratedInfrastructure] = None


def get_infrastructure(config: InfrastructureConfig = None) -> IntegratedInfrastructure:
    """
    Get infrastructure singleton

    Args:
        config: Infrastructure configuration (only used on first call)

    Returns:
        IntegratedInfrastructure instance
    """
    global _infrastructure_instance

    if _infrastructure_instance is None:
        _infrastructure_instance = IntegratedInfrastructure(config)

    return _infrastructure_instance


def initialize_infrastructure(config: InfrastructureConfig = None):
    """
    Initialize infrastructure (call once at app startup)

    Args:
        config: Infrastructure configuration
    """
    global _infrastructure_instance
    _infrastructure_instance = IntegratedInfrastructure(config)
    return _infrastructure_instance


# ============================================================================
# FASTAPI DEPENDENCY
# ============================================================================

def get_infra_dependency():
    """
    FastAPI dependency to inject infrastructure

    Usage:
        @app.get("/api/health")
        async def health_check(infra: IntegratedInfrastructure = Depends(get_infra_dependency)):
            return await infra.get_health_status()
    """
    return get_infrastructure()


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    import asyncio

    async def example_usage():
        print("\n" + "="*80)
        print("INFRASTRUCTURE INTEGRATION - DEMO")
        print("="*80)

        # Initialize infrastructure
        config = InfrastructureConfig()
        infra = initialize_infrastructure(config)

        # 1. Database operations
        print("\n1️⃣ Testing database operations...")
        async with infra.get_repository_context() as repo:
            # Example: Create user
            try:
                user = repo.users.create_user(
                    username="test_user",
                    email="test@example.com",
                    password_hash="hashed_password"
                )
                print(f"   ✅ Created user: {user.username}")
            except Exception as e:
                print(f"   ℹ️ User might already exist: {str(e)}")

        # 2. Production safeguards
        print("\n2️⃣ Testing production safeguards...")

        async def risky_operation():
            """Simulated risky operation"""
            print("   → Executing risky operation...")
            return {"success": True}

        result = await infra.production.execute_safe(risky_operation)
        print(f"   ✅ Operation result: {result}")

        # 3. Monitoring
        print("\n3️⃣ Recording metrics...")
        infra.monitoring.metrics.increment_counter("demo_operations", labels={"type": "test"})
        infra.monitoring.metrics.set_gauge("demo_value", 42.0)
        print(f"   ✅ Metrics recorded")

        # 4. Health check
        print("\n4️⃣ Checking system health...")
        health = await infra.get_health_status()
        print(f"   Overall status: {health['status']}")
        for component, status in health['components'].items():
            print(f"   - {component}: {status['status']} ({status['response_time_ms']:.1f}ms)")

        # 5. System metrics
        print("\n5️⃣ Getting system metrics...")
        metrics = infra.get_system_metrics()
        print(f"   CPU: {metrics['system']['cpu']['process_percent']:.1f}%")
        print(f"   Memory: {metrics['system']['memory']['rss_mb']:.1f} MB")
        print(f"   Rate limit status: {metrics['infrastructure']['rate_limiter']['requests_this_second']} requests/sec")

        print("\n" + "="*80)
        print("✅ INFRASTRUCTURE DEMO COMPLETE")
        print("="*80 + "\n")

    asyncio.run(example_usage())
