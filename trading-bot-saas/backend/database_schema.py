"""
Database Schema and ORM Models
Complete data persistence layer for the trading platform

Features:
- User management and authentication
- Bot configurations and state
- Trading signals and executions
- Position tracking and P&L
- Performance metrics and analytics
- Notification preferences
- Audit logs and system events

Database: PostgreSQL (production) / SQLite (development)
ORM: SQLAlchemy with async support
"""

from datetime import datetime
from typing import Optional, List, Dict
from enum import Enum as PyEnum
import json

from sqlalchemy import (
    create_engine, Column, Integer, String, Float, Boolean,
    DateTime, Text, JSON, ForeignKey, Enum, Index, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker as async_sessionmaker

Base = declarative_base()


# ============================================================================
# ENUMS
# ============================================================================

class BotStatus(PyEnum):
    """Bot operational status"""
    ACTIVE = "active"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


class SignalType(PyEnum):
    """Trading signal type"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


class OrderStatus(PyEnum):
    """Order execution status"""
    PENDING = "pending"
    OPEN = "open"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class PositionStatus(PyEnum):
    """Position status"""
    OPEN = "open"
    CLOSED = "closed"
    LIQUIDATED = "liquidated"


class NotificationChannel(PyEnum):
    """Notification delivery channel"""
    TELEGRAM = "telegram"
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    WEBHOOK = "webhook"


class TradeAction(PyEnum):
    """Trade action type"""
    ENTER = "enter"
    EXIT = "exit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"


# ============================================================================
# USER MANAGEMENT
# ============================================================================

class User(Base):
    """User accounts"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)

    # Profile
    full_name = Column(String(255))
    phone_number = Column(String(50))

    # Subscription
    subscription_tier = Column(String(50), default='free')  # free, basic, pro, enterprise
    subscription_expires_at = Column(DateTime, nullable=True)

    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)

    # Trader Classification
    capital_tier = Column(String(50))  # micro, small, medium, large, whale
    trading_style = Column(String(50))  # day_trader, swing_trader, etc.
    risk_profile = Column(String(50))  # conservative, moderate, aggressive

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)

    # Relationships
    bots = relationship('TradingBot', back_populates='user', cascade='all, delete-orphan')
    exchange_credentials = relationship('ExchangeCredential', back_populates='user', cascade='all, delete-orphan')
    notification_preferences = relationship('NotificationPreference', back_populates='user', cascade='all, delete-orphan')
    positions = relationship('Position', back_populates='user')
    trades = relationship('Trade', back_populates='user')

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', tier='{self.subscription_tier}')>"


class ExchangeCredential(Base):
    """Encrypted exchange API credentials"""
    __tablename__ = 'exchange_credentials'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    exchange_name = Column(String(50), nullable=False)  # binance, coinbase, etc.

    # Encrypted credentials (stored encrypted by SecureKeyVault)
    encrypted_api_key = Column(Text, nullable=False)
    encrypted_api_secret = Column(Text, nullable=False)
    encrypted_passphrase = Column(Text, nullable=True)  # For some exchanges

    # Settings
    is_testnet = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship('User', back_populates='exchange_credentials')

    __table_args__ = (
        UniqueConstraint('user_id', 'exchange_name', name='uq_user_exchange'),
        Index('idx_exchange_creds_user', 'user_id'),
    )

    def __repr__(self):
        return f"<ExchangeCredential(exchange='{self.exchange_name}', user_id={self.user_id})>"


# ============================================================================
# TRADING BOTS
# ============================================================================

class TradingBot(Base):
    """Trading bot configurations and state"""
    __tablename__ = 'trading_bots'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    # Configuration
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    exchange = Column(String(50), nullable=False)  # binance, coinbase, etc.
    symbols = Column(JSON, nullable=False)  # ["BTC/USDT", "ETH/USDT"]

    # Status
    status = Column(Enum(BotStatus), default=BotStatus.PAUSED)

    # Trading Parameters (stored as JSON for flexibility)
    parameters = Column(JSON, nullable=False)  # risk_per_trade, max_positions, etc.

    # Capital Management
    allocated_capital = Column(Float, nullable=False)
    available_capital = Column(Float, nullable=False)
    capital_in_use = Column(Float, default=0.0)

    # Performance Tracking
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    total_pnl = Column(Float, default=0.0)
    total_pnl_percent = Column(Float, default=0.0)

    # Daily Tracking
    today_trades = Column(Integer, default=0)
    today_pnl = Column(Float, default=0.0)
    last_trade_at = Column(DateTime, nullable=True)

    # Strategy
    strategy_type = Column(String(100))  # momentum, mean_reversion, ml_hybrid, etc.
    ml_model_version = Column(String(50), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    stopped_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship('User', back_populates='bots')
    signals = relationship('TradingSignal', back_populates='bot', cascade='all, delete-orphan')
    positions = relationship('Position', back_populates='bot')
    trades = relationship('Trade', back_populates='bot')
    performance_snapshots = relationship('PerformanceSnapshot', back_populates='bot', cascade='all, delete-orphan')

    __table_args__ = (
        Index('idx_bot_user', 'user_id'),
        Index('idx_bot_status', 'status'),
    )

    def __repr__(self):
        return f"<TradingBot(id={self.id}, name='{self.name}', status='{self.status.value}')>"


# ============================================================================
# TRADING SIGNALS
# ============================================================================

class TradingSignal(Base):
    """Trading signals generated by bots"""
    __tablename__ = 'trading_signals'

    id = Column(Integer, primary_key=True, autoincrement=True)
    bot_id = Column(Integer, ForeignKey('trading_bots.id'), nullable=False)

    # Signal Details
    symbol = Column(String(50), nullable=False)
    signal_type = Column(Enum(SignalType), nullable=False)

    # Pricing
    price = Column(Float, nullable=False)
    entry_price = Column(Float, nullable=True)
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)

    # Confidence & Analysis
    confidence_score = Column(Float, nullable=False)  # 0.0 - 1.0

    # Multi-factor scores
    ml_score = Column(Float, default=0.0)
    sentiment_score = Column(Float, default=0.0)
    whale_activity_score = Column(Float, default=0.0)
    technical_score = Column(Float, default=0.0)

    # Analysis data
    indicators = Column(JSON, nullable=True)  # RSI, MACD, etc.
    market_conditions = Column(JSON, nullable=True)  # volatility, trend, etc.

    # Position sizing
    recommended_size = Column(Float, nullable=True)
    risk_amount = Column(Float, nullable=True)

    # Execution
    is_executed = Column(Boolean, default=False)
    executed_at = Column(DateTime, nullable=True)

    # Timestamps
    generated_at = Column(DateTime, default=datetime.utcnow, index=True)
    expires_at = Column(DateTime, nullable=True)

    # Relationships
    bot = relationship('TradingBot', back_populates='signals')
    trades = relationship('Trade', back_populates='signal')

    __table_args__ = (
        Index('idx_signal_bot_time', 'bot_id', 'generated_at'),
        Index('idx_signal_symbol', 'symbol'),
        Index('idx_signal_executed', 'is_executed'),
    )

    def __repr__(self):
        return f"<TradingSignal(id={self.id}, symbol='{self.symbol}', type='{self.signal_type.value}', confidence={self.confidence_score:.2f})>"


# ============================================================================
# POSITIONS
# ============================================================================

class Position(Base):
    """Open and closed trading positions"""
    __tablename__ = 'positions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    bot_id = Column(Integer, ForeignKey('trading_bots.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    # Position Details
    symbol = Column(String(50), nullable=False)
    side = Column(String(10), nullable=False)  # long, short

    # Entry
    entry_price = Column(Float, nullable=False)
    size = Column(Float, nullable=False)  # Amount in base currency
    entry_capital = Column(Float, nullable=False)  # Capital used

    # Exit
    exit_price = Column(Float, nullable=True)
    exit_capital = Column(Float, nullable=True)

    # Risk Management
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)

    # Current State
    current_price = Column(Float, nullable=True)
    unrealized_pnl = Column(Float, default=0.0)
    unrealized_pnl_percent = Column(Float, default=0.0)

    # Realized P&L (when closed)
    realized_pnl = Column(Float, nullable=True)
    realized_pnl_percent = Column(Float, nullable=True)

    # Status
    status = Column(Enum(PositionStatus), default=PositionStatus.OPEN)

    # Fees
    entry_fee = Column(Float, default=0.0)
    exit_fee = Column(Float, default=0.0)
    total_fees = Column(Float, default=0.0)

    # Timestamps
    opened_at = Column(DateTime, default=datetime.utcnow, index=True)
    closed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    bot = relationship('TradingBot', back_populates='positions')
    user = relationship('User', back_populates='positions')
    trades = relationship('Trade', back_populates='position')

    __table_args__ = (
        Index('idx_position_bot_status', 'bot_id', 'status'),
        Index('idx_position_user', 'user_id'),
        Index('idx_position_symbol', 'symbol'),
    )

    def __repr__(self):
        return f"<Position(id={self.id}, symbol='{self.symbol}', side='{self.side}', status='{self.status.value}')>"


# ============================================================================
# TRADES
# ============================================================================

class Trade(Base):
    """Individual trade executions"""
    __tablename__ = 'trades'

    id = Column(Integer, primary_key=True, autoincrement=True)
    bot_id = Column(Integer, ForeignKey('trading_bots.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    signal_id = Column(Integer, ForeignKey('trading_signals.id'), nullable=True)
    position_id = Column(Integer, ForeignKey('positions.id'), nullable=True)

    # Trade Details
    symbol = Column(String(50), nullable=False)
    side = Column(String(10), nullable=False)  # buy, sell
    action = Column(Enum(TradeAction), nullable=False)  # enter, exit, stop_loss, take_profit

    # Execution
    order_type = Column(String(20), nullable=False)  # market, limit, stop_limit
    price = Column(Float, nullable=False)
    size = Column(Float, nullable=False)
    filled_size = Column(Float, default=0.0)

    # Cost
    cost = Column(Float, nullable=False)  # Total cost in quote currency
    fee = Column(Float, default=0.0)
    fee_currency = Column(String(10), default='USDT')

    # Order Status
    order_id = Column(String(255), nullable=True, index=True)  # Exchange order ID
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING)

    # Exchange Info
    exchange = Column(String(50), nullable=False)
    exchange_timestamp = Column(DateTime, nullable=True)

    # Error Handling
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    executed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    bot = relationship('TradingBot', back_populates='trades')
    user = relationship('User', back_populates='trades')
    signal = relationship('TradingSignal', back_populates='trades')
    position = relationship('Position', back_populates='trades')

    __table_args__ = (
        Index('idx_trade_bot_time', 'bot_id', 'created_at'),
        Index('idx_trade_user', 'user_id'),
        Index('idx_trade_symbol', 'symbol'),
        Index('idx_trade_status', 'status'),
    )

    def __repr__(self):
        return f"<Trade(id={self.id}, symbol='{self.symbol}', side='{self.side}', status='{self.status.value}')>"


# ============================================================================
# PERFORMANCE TRACKING
# ============================================================================

class PerformanceSnapshot(Base):
    """Periodic performance snapshots for analytics"""
    __tablename__ = 'performance_snapshots'

    id = Column(Integer, primary_key=True, autoincrement=True)
    bot_id = Column(Integer, ForeignKey('trading_bots.id'), nullable=False)

    # Snapshot period
    snapshot_type = Column(String(20), nullable=False)  # hourly, daily, weekly, monthly
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)

    # Trading Activity
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    win_rate = Column(Float, default=0.0)

    # P&L
    gross_profit = Column(Float, default=0.0)
    gross_loss = Column(Float, default=0.0)
    net_pnl = Column(Float, default=0.0)
    net_pnl_percent = Column(Float, default=0.0)

    # Risk Metrics
    max_drawdown = Column(Float, default=0.0)
    max_drawdown_percent = Column(Float, default=0.0)
    sharpe_ratio = Column(Float, nullable=True)
    profit_factor = Column(Float, nullable=True)

    # Trade Metrics
    avg_win = Column(Float, default=0.0)
    avg_loss = Column(Float, default=0.0)
    avg_win_percent = Column(Float, default=0.0)
    avg_loss_percent = Column(Float, default=0.0)
    largest_win = Column(Float, default=0.0)
    largest_loss = Column(Float, default=0.0)

    # Position Stats
    avg_position_duration = Column(Float, nullable=True)  # In seconds
    max_open_positions = Column(Integer, default=0)

    # Capital
    starting_capital = Column(Float, nullable=False)
    ending_capital = Column(Float, nullable=False)
    peak_capital = Column(Float, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    bot = relationship('TradingBot', back_populates='performance_snapshots')

    __table_args__ = (
        Index('idx_snapshot_bot_period', 'bot_id', 'snapshot_type', 'period_start'),
    )

    def __repr__(self):
        return f"<PerformanceSnapshot(bot_id={self.bot_id}, type='{self.snapshot_type}', pnl={self.net_pnl:.2f})>"


# ============================================================================
# NOTIFICATIONS
# ============================================================================

class NotificationPreference(Base):
    """User notification preferences"""
    __tablename__ = 'notification_preferences'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    # Channels
    telegram_enabled = Column(Boolean, default=False)
    telegram_chat_id = Column(String(255), nullable=True)

    email_enabled = Column(Boolean, default=True)
    email_address = Column(String(255), nullable=True)

    sms_enabled = Column(Boolean, default=False)
    sms_phone = Column(String(50), nullable=True)

    push_enabled = Column(Boolean, default=False)
    push_token = Column(Text, nullable=True)

    webhook_enabled = Column(Boolean, default=False)
    webhook_url = Column(Text, nullable=True)

    # Event Preferences
    notify_on_signals = Column(Boolean, default=True)
    notify_on_trades = Column(Boolean, default=True)
    notify_on_pnl_updates = Column(Boolean, default=False)
    notify_on_bot_status = Column(Boolean, default=True)
    notify_on_errors = Column(Boolean, default=True)

    # Thresholds
    min_signal_confidence = Column(Float, default=0.7)  # Only notify if confidence > threshold
    pnl_update_interval = Column(Integer, default=3600)  # Seconds between P&L updates

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship('User', back_populates='notification_preferences')

    __table_args__ = (
        Index('idx_notif_pref_user', 'user_id'),
    )


class NotificationLog(Base):
    """Log of sent notifications"""
    __tablename__ = 'notification_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    # Notification Details
    notification_type = Column(String(50), nullable=False)  # signal, trade, pnl, status, error
    channel = Column(Enum(NotificationChannel), nullable=False)

    # Content
    title = Column(String(500))
    message = Column(Text, nullable=False)
    data = Column(JSON, nullable=True)  # Additional structured data

    # Delivery Status
    status = Column(String(20), default='sent')  # sent, delivered, failed, bounced
    error_message = Column(Text, nullable=True)

    # Timestamps
    sent_at = Column(DateTime, default=datetime.utcnow, index=True)
    delivered_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index('idx_notif_log_user_time', 'user_id', 'sent_at'),
        Index('idx_notif_log_type', 'notification_type'),
    )


# ============================================================================
# SYSTEM LOGS
# ============================================================================

class SystemEvent(Base):
    """System events and audit logs"""
    __tablename__ = 'system_events'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Event Details
    event_type = Column(String(100), nullable=False, index=True)  # bot_started, trade_executed, error, etc.
    severity = Column(String(20), nullable=False)  # info, warning, error, critical

    # Context
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    bot_id = Column(Integer, ForeignKey('trading_bots.id'), nullable=True)

    # Message
    message = Column(Text, nullable=False)
    details = Column(JSON, nullable=True)  # Additional context

    # Stack trace for errors
    stack_trace = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index('idx_event_type_time', 'event_type', 'created_at'),
        Index('idx_event_severity', 'severity'),
        Index('idx_event_user', 'user_id'),
    )


class RateLimitLog(Base):
    """Rate limiting tracking"""
    __tablename__ = 'rate_limit_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Endpoint info
    endpoint = Column(String(255), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)

    # Request details
    request_count = Column(Integer, default=1)
    window_start = Column(DateTime, nullable=False)
    window_end = Column(DateTime, nullable=False)

    # Status
    limit_exceeded = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index('idx_rate_limit_endpoint_time', 'endpoint', 'created_at'),
    )


# ============================================================================
# DATABASE OPERATIONS
# ============================================================================

class DatabaseManager:
    """Database connection and session management"""

    def __init__(self, database_url: str, echo: bool = False):
        """
        Initialize database manager

        Args:
            database_url: Database connection URL
            echo: Echo SQL statements (for debugging)
        """
        self.database_url = database_url
        self.engine = None
        self.SessionLocal = None

        if database_url.startswith('sqlite'):
            # Synchronous SQLite
            self.engine = create_engine(database_url, echo=echo, connect_args={"check_same_thread": False})
            self.SessionLocal = sessionmaker(bind=self.engine, autocommit=False, autoflush=False)
        else:
            # Async PostgreSQL
            self.engine = create_async_engine(database_url, echo=echo)
            self.SessionLocal = async_sessionmaker(bind=self.engine, class_=AsyncSession, expire_on_commit=False)

    def create_all_tables(self):
        """Create all tables (synchronous)"""
        Base.metadata.create_all(bind=self.engine)
        print("✅ Database tables created successfully")

    def drop_all_tables(self):
        """Drop all tables (synchronous) - DANGER!"""
        Base.metadata.drop_all(bind=self.engine)
        print("⚠️ All database tables dropped")

    def get_session(self):
        """Get database session"""
        return self.SessionLocal()


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    # Development: SQLite
    db_manager = DatabaseManager("sqlite:///./trading_bot.db", echo=True)

    # Production: PostgreSQL
    # db_manager = DatabaseManager("postgresql+asyncpg://user:pass@localhost/trading_bot", echo=False)

    # Create tables
    db_manager.create_all_tables()

    print("\n" + "="*80)
    print("DATABASE SCHEMA CREATED")
    print("="*80)
    print("\n📊 Tables:")
    print("  - users")
    print("  - exchange_credentials")
    print("  - trading_bots")
    print("  - trading_signals")
    print("  - positions")
    print("  - trades")
    print("  - performance_snapshots")
    print("  - notification_preferences")
    print("  - notification_logs")
    print("  - system_events")
    print("  - rate_limit_logs")
    print("\n✅ Ready for production use")
