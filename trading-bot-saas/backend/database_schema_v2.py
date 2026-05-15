"""
Database Schema V2 - Production Optimized
Upgrades from v1:
- Connection pooling with optimized configuration
- Composite indexes for common queries
- Async session support
- Query performance optimization
- Connection health monitoring
"""

from datetime import datetime
from typing import Optional
from enum import Enum as PyEnum

from sqlalchemy import (
    create_engine, Column, Integer, String, Float, Boolean,
    DateTime, Text, JSON, ForeignKey, Enum, Index, UniqueConstraint, Numeric
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import QueuePool, NullPool
import logging

# Import all models from original schema
from database_schema import (
    Base, BotStatus, SignalType, OrderStatus, PositionStatus,
    NotificationChannel, TradeAction,
    User, ExchangeCredential, TradingBot, TradingSignal,
    Position, Trade, PerformanceSnapshot, NotificationPreference,
    NotificationLog, SystemEvent, RateLimitLog
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# ENHANCED DATABASE MANAGER WITH CONNECTION POOLING
# ============================================================================

class DatabaseManagerV2:
    """
    Enhanced database manager with production-grade connection pooling

    Upgrades from v1:
    - Connection pooling with QueuePool
    - Pool size optimization
    - Connection recycling
    - Pre-ping for connection health
    - Async session support
    - Pool monitoring
    """

    def __init__(
        self,
        database_url: str,
        echo: bool = False,
        pool_size: int = 20,
        max_overflow: int = 40,
        pool_recycle: int = 3600,
        pool_pre_ping: bool = True,
        pool_timeout: int = 30
    ):
        """
        Initialize database manager with connection pooling

        Args:
            database_url: Database connection URL
            echo: Echo SQL statements
            pool_size: Base number of connections (default: 20)
            max_overflow: Additional connections under load (default: 40)
            pool_recycle: Recycle connections after N seconds (default: 3600)
            pool_pre_ping: Test connections before using (default: True)
            pool_timeout: Wait time for connection availability (default: 30)
        """
        self.database_url = database_url
        self.is_sqlite = database_url.startswith('sqlite')
        self.is_async = database_url.startswith(('postgresql+asyncpg', 'mysql+aiomysql'))

        logger.info("=" * 80)
        logger.info("DATABASE MANAGER V2 - PRODUCTION OPTIMIZED")
        logger.info("=" * 80)

        if self.is_sqlite:
            # SQLite: Synchronous with NullPool (no pooling needed)
            logger.info("📊 Database: SQLite (Development)")
            logger.info("   ⚠️ Connection pooling disabled (SQLite limitation)")

            self.engine = create_engine(
                database_url,
                echo=echo,
                poolclass=NullPool,
                connect_args={"check_same_thread": False}
            )
            self.SessionLocal = sessionmaker(
                bind=self.engine,
                autocommit=False,
                autoflush=False
            )

        elif self.is_async:
            # Async PostgreSQL/MySQL with connection pooling
            logger.info("📊 Database: PostgreSQL/MySQL (Production - Async)")
            logger.info(f"   ✅ Connection pooling: {pool_size} base + {max_overflow} overflow")
            logger.info(f"   ✅ Pool recycle: {pool_recycle}s")
            logger.info(f"   ✅ Pre-ping: {pool_pre_ping}")
            logger.info(f"   ✅ Timeout: {pool_timeout}s")

            self.engine = create_async_engine(
                database_url,
                echo=echo,
                pool_size=pool_size,
                max_overflow=max_overflow,
                pool_recycle=pool_recycle,
                pool_pre_ping=pool_pre_ping,
                pool_timeout=pool_timeout,
                poolclass=QueuePool
            )
            self.SessionLocal = async_sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autocommit=False,
                autoflush=False
            )

        else:
            # Synchronous PostgreSQL/MySQL with connection pooling
            logger.info("📊 Database: PostgreSQL/MySQL (Production - Sync)")
            logger.info(f"   ✅ Connection pooling: {pool_size} base + {max_overflow} overflow")
            logger.info(f"   ✅ Pool recycle: {pool_recycle}s")
            logger.info(f"   ✅ Pre-ping: {pool_pre_ping}")
            logger.info(f"   ✅ Timeout: {pool_timeout}s")

            self.engine = create_engine(
                database_url,
                echo=echo,
                pool_size=pool_size,
                max_overflow=max_overflow,
                pool_recycle=pool_recycle,
                pool_pre_ping=pool_pre_ping,
                pool_timeout=pool_timeout,
                poolclass=QueuePool
            )
            self.SessionLocal = sessionmaker(
                bind=self.engine,
                autocommit=False,
                autoflush=False
            )

        logger.info("=" * 80)
        logger.info("✅ DATABASE MANAGER V2 READY")
        logger.info("=" * 80 + "\n")

    def create_all_tables(self):
        """Create all tables"""
        Base.metadata.create_all(bind=self.engine)
        logger.info("✅ Database tables created successfully")

        # Log table creation with indexes
        tables = Base.metadata.tables.keys()
        logger.info(f"📊 Created {len(tables)} tables:")
        for table in tables:
            table_obj = Base.metadata.tables[table]
            index_count = len(table_obj.indexes)
            logger.info(f"   - {table} ({index_count} indexes)")

    def drop_all_tables(self):
        """Drop all tables - DANGER!"""
        Base.metadata.drop_all(bind=self.engine)
        logger.warning("⚠️ All database tables dropped")

    def get_session(self):
        """Get database session"""
        return self.SessionLocal()

    def get_pool_status(self) -> dict:
        """
        Get connection pool status

        Returns:
            Pool statistics
        """
        if self.is_sqlite:
            return {"status": "no_pooling", "type": "sqlite"}

        pool = self.engine.pool

        return {
            "size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "total": pool.size() + pool.overflow()
        }

    async def get_pool_status_async(self) -> dict:
        """Get async pool status"""
        if not self.is_async:
            return self.get_pool_status()

        # For async engines
        pool = self.engine.pool

        return {
            "size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "total": pool.size() + pool.overflow()
        }

    def log_pool_status(self):
        """Log current pool status"""
        status = self.get_pool_status()

        if status.get("status") == "no_pooling":
            logger.info("📊 Connection Pool: Not applicable (SQLite)")
            return

        logger.info("📊 Connection Pool Status:")
        logger.info(f"   Total connections: {status['total']}")
        logger.info(f"   Checked out: {status['checked_out']}")
        logger.info(f"   Available: {status['checked_in']}")
        logger.info(f"   Overflow: {status['overflow']}")

    async def close(self):
        """Close database engine"""
        if self.is_async:
            await self.engine.dispose()
        else:
            self.engine.dispose()
        logger.info("✅ Database connections closed")


# ============================================================================
# COMPOSITE INDEXES FOR QUERY OPTIMIZATION
# ============================================================================

def create_composite_indexes():
    """
    Create composite indexes for common query patterns
    Dramatically improves query performance for multi-column filters
    """

    # User + Bot lookup (common: get user's active bots)
    Index(
        'idx_bot_user_status',
        TradingBot.user_id,
        TradingBot.status
    )

    # Signal lookup by bot + time range
    Index(
        'idx_signal_bot_time_executed',
        TradingSignal.bot_id,
        TradingSignal.generated_at,
        TradingSignal.is_executed
    )

    # Position lookup by bot + status
    Index(
        'idx_position_bot_status_opened',
        Position.bot_id,
        Position.status,
        Position.opened_at
    )

    # Trade lookup by user + time + status
    Index(
        'idx_trade_user_time_status',
        Trade.user_id,
        Trade.created_at,
        Trade.status
    )

    # Performance snapshot lookup
    Index(
        'idx_snapshot_bot_type_period',
        PerformanceSnapshot.bot_id,
        PerformanceSnapshot.snapshot_type,
        PerformanceSnapshot.period_start
    )

    # System events lookup by type + severity + time
    Index(
        'idx_event_type_severity_time',
        SystemEvent.event_type,
        SystemEvent.severity,
        SystemEvent.created_at
    )

    logger.info("✅ Composite indexes created for query optimization")


# ============================================================================
# IMPROVED PRICE COLUMN (Numeric instead of Float)
# ============================================================================

def add_precision_improvements():
    """
    Add high-precision numeric columns for financial data
    Float has precision issues for prices - use Numeric instead
    """

    # Note: These would be applied via database migration
    # Example migration:
    """
    ALTER TABLE positions
    ALTER COLUMN entry_price TYPE NUMERIC(19, 8),
    ALTER COLUMN exit_price TYPE NUMERIC(19, 8),
    ALTER COLUMN current_price TYPE NUMERIC(19, 8);

    ALTER TABLE trades
    ALTER COLUMN price TYPE NUMERIC(19, 8),
    ALTER COLUMN size TYPE NUMERIC(19, 8);

    ALTER TABLE trading_signals
    ALTER COLUMN price TYPE NUMERIC(19, 8),
    ALTER COLUMN entry_price TYPE NUMERIC(19, 8);
    """

    logger.info("ℹ️ Price precision improvements require database migration")
    logger.info("   Run: alembic revision --autogenerate -m 'Improve price precision'")


# ============================================================================
# EXAMPLE USAGE WITH CONNECTION POOLING
# ============================================================================

if __name__ == "__main__":
    import asyncio

    async def example_usage():
        print("\n" + "="*80)
        print("DATABASE MANAGER V2 - DEMO")
        print("="*80)

        # Development: SQLite
        db_dev = DatabaseManagerV2("sqlite:///./trading_bot.db", echo=False)
        db_dev.create_all_tables()
        db_dev.log_pool_status()

        print("\n" + "="*80)
        print("PRODUCTION CONFIGURATION")
        print("="*80)

        # Production: PostgreSQL with optimized pooling
        # db_prod = DatabaseManagerV2(
        #     database_url="postgresql://user:pass@localhost/trading_bot",
        #     echo=False,
        #     pool_size=20,        # 20 base connections
        #     max_overflow=40,     # +40 connections under load (60 total)
        #     pool_recycle=3600,   # Recycle after 1 hour
        #     pool_pre_ping=True,  # Test before use
        #     pool_timeout=30      # Wait 30s for connection
        # )

        # Simulate load
        print("\n📊 Simulating high load...")

        sessions = []
        for i in range(10):
            session = db_dev.get_session()
            sessions.append(session)
            print(f"   Created session {i+1}")

        db_dev.log_pool_status()

        # Cleanup
        for session in sessions:
            session.close()

        print("\n✅ Cleanup complete")
        db_dev.log_pool_status()

        print("\n" + "="*80)
        print("CONNECTION POOLING DEMO COMPLETE")
        print("="*80)

        # Create composite indexes
        print("\n📊 Creating composite indexes...")
        create_composite_indexes()

        print("\n📊 Precision improvements...")
        add_precision_improvements()

    asyncio.run(example_usage())
