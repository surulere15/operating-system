"""
Database configuration and models for Trading Bot SaaS
Multi-tenant architecture with encrypted API keys
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, JSON, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os
from cryptography.fernet import Fernet

# Database URL (from environment)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/trading_bot_saas")

# Create engine
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Encryption for API keys
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", Fernet.generate_key())
cipher_suite = Fernet(ENCRYPTION_KEY)


def encrypt_value(value: str) -> str:
    """Encrypt sensitive data"""
    return cipher_suite.encrypt(value.encode()).decode()


def decrypt_value(encrypted_value: str) -> str:
    """Decrypt sensitive data"""
    return cipher_suite.decrypt(encrypted_value.encode()).decode()


# ============================================================================
# DATABASE MODELS
# ============================================================================

class User(Base):
    """User account"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)

    # Subscription
    tier = Column(String, default="starter")  # starter, pro, elite, enterprise
    stripe_customer_id = Column(String, unique=True)
    subscription_status = Column(String, default="inactive")  # inactive, active, past_due, canceled

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime)

    # Settings
    telegram_chat_id = Column(String)
    email_notifications = Column(Boolean, default=True)
    sms_notifications = Column(Boolean, default=False)

    # Relationships
    bots = relationship("Bot", back_populates="user", cascade="all, delete-orphan")
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    trades = relationship("Trade", back_populates="user", cascade="all, delete-orphan")
    subscriptions = relationship("Subscription", back_populates="user", cascade="all, delete-orphan")


class Bot(Base):
    """User's bot instance"""
    __tablename__ = "bots"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Bot config
    name = Column(String, nullable=False)
    status = Column(String, default="inactive")  # inactive, active, paused, error
    exchange = Column(String, default="bybit")  # bybit, binance, okx

    # Trading config (stored as JSON)
    config = Column(JSON, default={
        "markets": ["BTC/USDT", "ETH/USDT", "SOL/USDT"],
        "leverage": {"BTC/USDT": 15, "ETH/USDT": 15, "SOL/USDT": 20},
        "confidence_threshold": 60,
        "max_daily_loss": 10,
        "max_position_loss": 3,
        "scan_interval": 300
    })

    # Capital
    capital = Column(Float, default=35.0)
    current_balance = Column(Float, default=0.0)

    # Stats
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    total_pnl = Column(Float, default=0.0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_trade_at = Column(DateTime)

    # Relationships
    user = relationship("User", back_populates="bots")
    trades = relationship("Trade", back_populates="bot", cascade="all, delete-orphan")


class APIKey(Base):
    """Encrypted exchange API keys"""
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    exchange = Column(String, nullable=False)  # bybit, binance, okx

    # Encrypted credentials
    api_key_encrypted = Column(Text, nullable=False)
    api_secret_encrypted = Column(Text, nullable=False)

    # Metadata
    is_testnet = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime)

    # Relationships
    user = relationship("User", back_populates="api_keys")

    def set_api_key(self, api_key: str):
        """Encrypt and store API key"""
        self.api_key_encrypted = encrypt_value(api_key)

    def set_api_secret(self, api_secret: str):
        """Encrypt and store API secret"""
        self.api_secret_encrypted = encrypt_value(api_secret)

    def get_api_key(self) -> str:
        """Decrypt and return API key"""
        return decrypt_value(self.api_key_encrypted)

    def get_api_secret(self) -> str:
        """Decrypt and return API secret"""
        return decrypt_value(self.api_secret_encrypted)


class Trade(Base):
    """Trade records"""
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    bot_id = Column(Integer, ForeignKey("bots.id"), nullable=False)

    # Trade details
    symbol = Column(String, nullable=False)
    side = Column(String, nullable=False)  # BUY, SELL

    # Prices
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float)
    stop_loss = Column(Float)
    take_profit_1 = Column(Float)
    take_profit_2 = Column(Float)
    take_profit_3 = Column(Float)

    # Position
    quantity = Column(Float, nullable=False)
    leverage = Column(Integer, nullable=False)
    position_size = Column(Float, nullable=False)

    # Results
    pnl = Column(Float)
    pnl_percentage = Column(Float)
    status = Column(String, default="open")  # open, closed, stopped

    # Signal info
    confidence = Column(Integer, nullable=False)
    indicators = Column(JSON)  # RSI, MACD, volume, etc.
    reason = Column(Text)

    # Timestamps
    opened_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    closed_at = Column(DateTime)

    # Relationships
    user = relationship("User", back_populates="trades")
    bot = relationship("Bot", back_populates="trades")


class Subscription(Base):
    """Subscription history"""
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Stripe
    stripe_subscription_id = Column(String, unique=True)
    stripe_price_id = Column(String)

    # Plan
    tier = Column(String, nullable=False)
    status = Column(String, nullable=False)  # active, canceled, past_due, incomplete

    # Billing
    current_period_start = Column(DateTime)
    current_period_end = Column(DateTime)
    cancel_at_period_end = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="subscriptions")


# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================

def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created")


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


if __name__ == "__main__":
    # Create tables
    init_db()
