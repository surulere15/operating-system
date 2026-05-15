"""
Database Operations and Repository Pattern
Clean CRUD operations for all database entities

Features:
- Repository classes for each entity
- Transaction management
- Bulk operations
- Query helpers
- Data validation
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import and_, or_, desc, func
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from database_schema import (
    User, ExchangeCredential, TradingBot, TradingSignal,
    Position, Trade, PerformanceSnapshot, NotificationPreference,
    NotificationLog, SystemEvent, RateLimitLog,
    BotStatus, SignalType, OrderStatus, PositionStatus,
    NotificationChannel, TradeAction
)


# ============================================================================
# BASE REPOSITORY
# ============================================================================

class BaseRepository:
    """Base repository with common operations"""

    def __init__(self, session: Session):
        self.session = session

    def commit(self):
        """Commit transaction"""
        try:
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def rollback(self):
        """Rollback transaction"""
        self.session.rollback()

    def refresh(self, instance):
        """Refresh instance from database"""
        self.session.refresh(instance)


# ============================================================================
# USER REPOSITORY
# ============================================================================

class UserRepository(BaseRepository):
    """User data operations"""

    def create_user(self, username: str, email: str, password_hash: str, **kwargs) -> User:
        """Create new user"""
        user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            **kwargs
        )
        self.session.add(user)
        self.commit()
        self.refresh(user)
        return user

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return self.session.query(User).filter(User.id == user_id).first()

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        return self.session.query(User).filter(User.username == username).first()

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.session.query(User).filter(User.email == email).first()

    def update_user(self, user_id: int, **kwargs) -> Optional[User]:
        """Update user"""
        user = self.get_user_by_id(user_id)
        if user:
            for key, value in kwargs.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            user.updated_at = datetime.utcnow()
            self.commit()
            self.refresh(user)
        return user

    def update_last_login(self, user_id: int):
        """Update last login timestamp"""
        user = self.get_user_by_id(user_id)
        if user:
            user.last_login_at = datetime.utcnow()
            self.commit()

    def get_all_active_users(self) -> List[User]:
        """Get all active users"""
        return self.session.query(User).filter(User.is_active == True).all()


# ============================================================================
# EXCHANGE CREDENTIALS REPOSITORY
# ============================================================================

class ExchangeCredentialRepository(BaseRepository):
    """Exchange credential operations"""

    def store_credentials(self, user_id: int, exchange_name: str,
                         encrypted_api_key: str, encrypted_api_secret: str,
                         encrypted_passphrase: str = None, is_testnet: bool = False) -> ExchangeCredential:
        """Store exchange credentials"""
        cred = ExchangeCredential(
            user_id=user_id,
            exchange_name=exchange_name,
            encrypted_api_key=encrypted_api_key,
            encrypted_api_secret=encrypted_api_secret,
            encrypted_passphrase=encrypted_passphrase,
            is_testnet=is_testnet
        )
        self.session.add(cred)
        self.commit()
        self.refresh(cred)
        return cred

    def get_credentials(self, user_id: int, exchange_name: str) -> Optional[ExchangeCredential]:
        """Get credentials for user and exchange"""
        return self.session.query(ExchangeCredential).filter(
            and_(
                ExchangeCredential.user_id == user_id,
                ExchangeCredential.exchange_name == exchange_name,
                ExchangeCredential.is_active == True
            )
        ).first()

    def get_all_user_credentials(self, user_id: int) -> List[ExchangeCredential]:
        """Get all credentials for user"""
        return self.session.query(ExchangeCredential).filter(
            and_(
                ExchangeCredential.user_id == user_id,
                ExchangeCredential.is_active == True
            )
        ).all()

    def update_last_used(self, cred_id: int):
        """Update last used timestamp"""
        cred = self.session.query(ExchangeCredential).filter(ExchangeCredential.id == cred_id).first()
        if cred:
            cred.last_used_at = datetime.utcnow()
            self.commit()

    def deactivate_credentials(self, cred_id: int):
        """Deactivate credentials"""
        cred = self.session.query(ExchangeCredential).filter(ExchangeCredential.id == cred_id).first()
        if cred:
            cred.is_active = False
            self.commit()


# ============================================================================
# TRADING BOT REPOSITORY
# ============================================================================

class TradingBotRepository(BaseRepository):
    """Trading bot operations"""

    def create_bot(self, user_id: int, name: str, exchange: str,
                   symbols: List[str], parameters: Dict, allocated_capital: float) -> TradingBot:
        """Create new trading bot"""
        bot = TradingBot(
            user_id=user_id,
            name=name,
            exchange=exchange,
            symbols=symbols,
            parameters=parameters,
            allocated_capital=allocated_capital,
            available_capital=allocated_capital
        )
        self.session.add(bot)
        self.commit()
        self.refresh(bot)
        return bot

    def get_bot_by_id(self, bot_id: int) -> Optional[TradingBot]:
        """Get bot by ID"""
        return self.session.query(TradingBot).filter(TradingBot.id == bot_id).first()

    def get_user_bots(self, user_id: int) -> List[TradingBot]:
        """Get all bots for user"""
        return self.session.query(TradingBot).filter(TradingBot.user_id == user_id).all()

    def get_active_bots(self, user_id: int = None) -> List[TradingBot]:
        """Get active bots"""
        query = self.session.query(TradingBot).filter(TradingBot.status == BotStatus.ACTIVE)
        if user_id:
            query = query.filter(TradingBot.user_id == user_id)
        return query.all()

    def update_bot_status(self, bot_id: int, status: BotStatus):
        """Update bot status"""
        bot = self.get_bot_by_id(bot_id)
        if bot:
            bot.status = status
            if status == BotStatus.ACTIVE:
                bot.started_at = datetime.utcnow()
            elif status in [BotStatus.STOPPED, BotStatus.PAUSED]:
                bot.stopped_at = datetime.utcnow()
            bot.updated_at = datetime.utcnow()
            self.commit()

    def update_bot_capital(self, bot_id: int, available_capital: float, capital_in_use: float):
        """Update bot capital"""
        bot = self.get_bot_by_id(bot_id)
        if bot:
            bot.available_capital = available_capital
            bot.capital_in_use = capital_in_use
            bot.updated_at = datetime.utcnow()
            self.commit()

    def update_bot_performance(self, bot_id: int, trade_result: Dict):
        """Update bot performance after trade"""
        bot = self.get_bot_by_id(bot_id)
        if bot:
            bot.total_trades += 1
            if trade_result['pnl'] > 0:
                bot.winning_trades += 1
            else:
                bot.losing_trades += 1

            bot.total_pnl += trade_result['pnl']
            bot.total_pnl_percent = (bot.total_pnl / bot.allocated_capital) * 100

            bot.today_trades += 1
            bot.today_pnl += trade_result['pnl']
            bot.last_trade_at = datetime.utcnow()
            bot.updated_at = datetime.utcnow()

            self.commit()

    def reset_daily_stats(self, bot_id: int):
        """Reset daily statistics"""
        bot = self.get_bot_by_id(bot_id)
        if bot:
            bot.today_trades = 0
            bot.today_pnl = 0.0
            self.commit()


# ============================================================================
# TRADING SIGNAL REPOSITORY
# ============================================================================

class TradingSignalRepository(BaseRepository):
    """Trading signal operations"""

    def create_signal(self, bot_id: int, symbol: str, signal_type: SignalType,
                     price: float, confidence_score: float, **kwargs) -> TradingSignal:
        """Create new trading signal"""
        signal = TradingSignal(
            bot_id=bot_id,
            symbol=symbol,
            signal_type=signal_type,
            price=price,
            confidence_score=confidence_score,
            **kwargs
        )
        self.session.add(signal)
        self.commit()
        self.refresh(signal)
        return signal

    def get_signal_by_id(self, signal_id: int) -> Optional[TradingSignal]:
        """Get signal by ID"""
        return self.session.query(TradingSignal).filter(TradingSignal.id == signal_id).first()

    def get_bot_signals(self, bot_id: int, limit: int = 100) -> List[TradingSignal]:
        """Get recent signals for bot"""
        return self.session.query(TradingSignal).filter(
            TradingSignal.bot_id == bot_id
        ).order_by(desc(TradingSignal.generated_at)).limit(limit).all()

    def get_unexecuted_signals(self, bot_id: int) -> List[TradingSignal]:
        """Get unexecuted signals"""
        return self.session.query(TradingSignal).filter(
            and_(
                TradingSignal.bot_id == bot_id,
                TradingSignal.is_executed == False,
                or_(
                    TradingSignal.expires_at == None,
                    TradingSignal.expires_at > datetime.utcnow()
                )
            )
        ).all()

    def mark_signal_executed(self, signal_id: int):
        """Mark signal as executed"""
        signal = self.get_signal_by_id(signal_id)
        if signal:
            signal.is_executed = True
            signal.executed_at = datetime.utcnow()
            self.commit()

    def get_signals_by_confidence(self, bot_id: int, min_confidence: float) -> List[TradingSignal]:
        """Get signals above confidence threshold"""
        return self.session.query(TradingSignal).filter(
            and_(
                TradingSignal.bot_id == bot_id,
                TradingSignal.confidence_score >= min_confidence
            )
        ).order_by(desc(TradingSignal.generated_at)).all()


# ============================================================================
# POSITION REPOSITORY
# ============================================================================

class PositionRepository(BaseRepository):
    """Position operations"""

    def open_position(self, bot_id: int, user_id: int, symbol: str, side: str,
                     entry_price: float, size: float, entry_capital: float, **kwargs) -> Position:
        """Open new position"""
        position = Position(
            bot_id=bot_id,
            user_id=user_id,
            symbol=symbol,
            side=side,
            entry_price=entry_price,
            size=size,
            entry_capital=entry_capital,
            status=PositionStatus.OPEN,
            **kwargs
        )
        self.session.add(position)
        self.commit()
        self.refresh(position)
        return position

    def get_position_by_id(self, position_id: int) -> Optional[Position]:
        """Get position by ID"""
        return self.session.query(Position).filter(Position.id == position_id).first()

    def get_open_positions(self, bot_id: int = None, user_id: int = None) -> List[Position]:
        """Get open positions"""
        query = self.session.query(Position).filter(Position.status == PositionStatus.OPEN)

        if bot_id:
            query = query.filter(Position.bot_id == bot_id)
        if user_id:
            query = query.filter(Position.user_id == user_id)

        return query.all()

    def update_position_price(self, position_id: int, current_price: float):
        """Update position with current price and unrealized P&L"""
        position = self.get_position_by_id(position_id)
        if position and position.status == PositionStatus.OPEN:
            position.current_price = current_price

            # Calculate unrealized P&L
            if position.side == 'long':
                position.unrealized_pnl = (current_price - position.entry_price) * position.size
            else:  # short
                position.unrealized_pnl = (position.entry_price - current_price) * position.size

            position.unrealized_pnl_percent = (position.unrealized_pnl / position.entry_capital) * 100
            position.updated_at = datetime.utcnow()

            self.commit()

    def close_position(self, position_id: int, exit_price: float, exit_capital: float, exit_fee: float = 0.0):
        """Close position"""
        position = self.get_position_by_id(position_id)
        if position:
            position.exit_price = exit_price
            position.exit_capital = exit_capital
            position.exit_fee = exit_fee
            position.total_fees = position.entry_fee + position.exit_fee

            # Calculate realized P&L
            position.realized_pnl = exit_capital - position.entry_capital - position.total_fees
            position.realized_pnl_percent = (position.realized_pnl / position.entry_capital) * 100

            position.status = PositionStatus.CLOSED
            position.closed_at = datetime.utcnow()
            position.updated_at = datetime.utcnow()

            self.commit()
            self.refresh(position)

        return position

    def get_position_history(self, bot_id: int = None, user_id: int = None,
                            start_date: datetime = None, end_date: datetime = None) -> List[Position]:
        """Get position history"""
        query = self.session.query(Position)

        if bot_id:
            query = query.filter(Position.bot_id == bot_id)
        if user_id:
            query = query.filter(Position.user_id == user_id)
        if start_date:
            query = query.filter(Position.opened_at >= start_date)
        if end_date:
            query = query.filter(Position.opened_at <= end_date)

        return query.order_by(desc(Position.opened_at)).all()


# ============================================================================
# TRADE REPOSITORY
# ============================================================================

class TradeRepository(BaseRepository):
    """Trade operations"""

    def create_trade(self, bot_id: int, user_id: int, symbol: str, side: str,
                    action: TradeAction, order_type: str, price: float, size: float,
                    cost: float, exchange: str, **kwargs) -> Trade:
        """Create new trade"""
        trade = Trade(
            bot_id=bot_id,
            user_id=user_id,
            symbol=symbol,
            side=side,
            action=action,
            order_type=order_type,
            price=price,
            size=size,
            cost=cost,
            exchange=exchange,
            **kwargs
        )
        self.session.add(trade)
        self.commit()
        self.refresh(trade)
        return trade

    def get_trade_by_id(self, trade_id: int) -> Optional[Trade]:
        """Get trade by ID"""
        return self.session.query(Trade).filter(Trade.id == trade_id).first()

    def get_trade_by_order_id(self, order_id: str) -> Optional[Trade]:
        """Get trade by exchange order ID"""
        return self.session.query(Trade).filter(Trade.order_id == order_id).first()

    def update_trade_status(self, trade_id: int, status: OrderStatus, filled_size: float = None, **kwargs):
        """Update trade status"""
        trade = self.get_trade_by_id(trade_id)
        if trade:
            trade.status = status
            if filled_size is not None:
                trade.filled_size = filled_size

            if status == OrderStatus.FILLED:
                trade.executed_at = datetime.utcnow()

            for key, value in kwargs.items():
                if hasattr(trade, key):
                    setattr(trade, key, value)

            trade.updated_at = datetime.utcnow()
            self.commit()

    def get_bot_trades(self, bot_id: int, limit: int = 100) -> List[Trade]:
        """Get recent trades for bot"""
        return self.session.query(Trade).filter(
            Trade.bot_id == bot_id
        ).order_by(desc(Trade.created_at)).limit(limit).all()

    def get_filled_trades(self, bot_id: int = None, user_id: int = None,
                         start_date: datetime = None, end_date: datetime = None) -> List[Trade]:
        """Get filled trades"""
        query = self.session.query(Trade).filter(Trade.status == OrderStatus.FILLED)

        if bot_id:
            query = query.filter(Trade.bot_id == bot_id)
        if user_id:
            query = query.filter(Trade.user_id == user_id)
        if start_date:
            query = query.filter(Trade.created_at >= start_date)
        if end_date:
            query = query.filter(Trade.created_at <= end_date)

        return query.order_by(desc(Trade.executed_at)).all()

    def get_pending_trades(self, bot_id: int) -> List[Trade]:
        """Get pending trades"""
        return self.session.query(Trade).filter(
            and_(
                Trade.bot_id == bot_id,
                Trade.status.in_([OrderStatus.PENDING, OrderStatus.OPEN])
            )
        ).all()


# ============================================================================
# PERFORMANCE REPOSITORY
# ============================================================================

class PerformanceRepository(BaseRepository):
    """Performance snapshot operations"""

    def create_snapshot(self, bot_id: int, snapshot_type: str,
                       period_start: datetime, period_end: datetime,
                       metrics: Dict) -> PerformanceSnapshot:
        """Create performance snapshot"""
        snapshot = PerformanceSnapshot(
            bot_id=bot_id,
            snapshot_type=snapshot_type,
            period_start=period_start,
            period_end=period_end,
            **metrics
        )
        self.session.add(snapshot)
        self.commit()
        self.refresh(snapshot)
        return snapshot

    def get_latest_snapshot(self, bot_id: int, snapshot_type: str) -> Optional[PerformanceSnapshot]:
        """Get latest snapshot"""
        return self.session.query(PerformanceSnapshot).filter(
            and_(
                PerformanceSnapshot.bot_id == bot_id,
                PerformanceSnapshot.snapshot_type == snapshot_type
            )
        ).order_by(desc(PerformanceSnapshot.period_end)).first()

    def get_snapshots(self, bot_id: int, snapshot_type: str,
                     start_date: datetime = None, end_date: datetime = None) -> List[PerformanceSnapshot]:
        """Get performance snapshots"""
        query = self.session.query(PerformanceSnapshot).filter(
            and_(
                PerformanceSnapshot.bot_id == bot_id,
                PerformanceSnapshot.snapshot_type == snapshot_type
            )
        )

        if start_date:
            query = query.filter(PerformanceSnapshot.period_start >= start_date)
        if end_date:
            query = query.filter(PerformanceSnapshot.period_end <= end_date)

        return query.order_by(PerformanceSnapshot.period_start).all()


# ============================================================================
# NOTIFICATION REPOSITORY
# ============================================================================

class NotificationRepository(BaseRepository):
    """Notification operations"""

    def get_user_preferences(self, user_id: int) -> Optional[NotificationPreference]:
        """Get user notification preferences"""
        return self.session.query(NotificationPreference).filter(
            NotificationPreference.user_id == user_id
        ).first()

    def update_preferences(self, user_id: int, **kwargs) -> NotificationPreference:
        """Update notification preferences"""
        prefs = self.get_user_preferences(user_id)

        if not prefs:
            prefs = NotificationPreference(user_id=user_id)
            self.session.add(prefs)

        for key, value in kwargs.items():
            if hasattr(prefs, key):
                setattr(prefs, key, value)

        prefs.updated_at = datetime.utcnow()
        self.commit()
        self.refresh(prefs)
        return prefs

    def log_notification(self, user_id: int, notification_type: str,
                        channel: NotificationChannel, message: str, **kwargs) -> NotificationLog:
        """Log sent notification"""
        log = NotificationLog(
            user_id=user_id,
            notification_type=notification_type,
            channel=channel,
            message=message,
            **kwargs
        )
        self.session.add(log)
        self.commit()
        return log

    def get_recent_notifications(self, user_id: int, hours: int = 24) -> List[NotificationLog]:
        """Get recent notifications"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        return self.session.query(NotificationLog).filter(
            and_(
                NotificationLog.user_id == user_id,
                NotificationLog.sent_at >= cutoff
            )
        ).order_by(desc(NotificationLog.sent_at)).all()


# ============================================================================
# SYSTEM EVENT REPOSITORY
# ============================================================================

class SystemEventRepository(BaseRepository):
    """System event logging"""

    def log_event(self, event_type: str, severity: str, message: str,
                 user_id: int = None, bot_id: int = None, **kwargs) -> SystemEvent:
        """Log system event"""
        event = SystemEvent(
            event_type=event_type,
            severity=severity,
            message=message,
            user_id=user_id,
            bot_id=bot_id,
            **kwargs
        )
        self.session.add(event)
        self.commit()
        return event

    def get_recent_events(self, event_type: str = None, severity: str = None,
                         hours: int = 24, limit: int = 100) -> List[SystemEvent]:
        """Get recent system events"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        query = self.session.query(SystemEvent).filter(SystemEvent.created_at >= cutoff)

        if event_type:
            query = query.filter(SystemEvent.event_type == event_type)
        if severity:
            query = query.filter(SystemEvent.severity == severity)

        return query.order_by(desc(SystemEvent.created_at)).limit(limit).all()

    def get_error_count(self, hours: int = 24) -> int:
        """Get error count"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        return self.session.query(SystemEvent).filter(
            and_(
                SystemEvent.severity.in_(['error', 'critical']),
                SystemEvent.created_at >= cutoff
            )
        ).count()


# ============================================================================
# AGGREGATE REPOSITORY (Convenience)
# ============================================================================

class TradingRepository:
    """Aggregate repository with all operations"""

    def __init__(self, session: Session):
        self.session = session

        # Initialize all repositories
        self.users = UserRepository(session)
        self.credentials = ExchangeCredentialRepository(session)
        self.bots = TradingBotRepository(session)
        self.signals = TradingSignalRepository(session)
        self.positions = PositionRepository(session)
        self.trades = TradeRepository(session)
        self.performance = PerformanceRepository(session)
        self.notifications = NotificationRepository(session)
        self.events = SystemEventRepository(session)

    def commit(self):
        """Commit all changes"""
        self.session.commit()

    def rollback(self):
        """Rollback all changes"""
        self.session.rollback()

    def close(self):
        """Close session"""
        self.session.close()


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    from database_schema import DatabaseManager

    # Initialize database
    db_manager = DatabaseManager("sqlite:///./trading_bot.db")
    session = db_manager.get_session()

    # Create repository
    repo = TradingRepository(session)

    print("\n" + "="*80)
    print("DATABASE OPERATIONS - DEMO")
    print("="*80)

    # Create user
    user = repo.users.create_user(
        username="test_trader",
        email="trader@example.com",
        password_hash="hashed_password_here",
        full_name="Test Trader",
        capital_tier="medium",
        trading_style="day_trader",
        risk_profile="moderate"
    )
    print(f"\n✅ Created user: {user}")

    # Create bot
    bot = repo.bots.create_bot(
        user_id=user.id,
        name="BTC Momentum Bot",
        exchange="binance",
        symbols=["BTC/USDT", "ETH/USDT"],
        parameters={
            "risk_per_trade": 0.02,
            "max_positions": 3,
            "stop_loss_percent": 2.0,
            "take_profit_percent": 4.0
        },
        allocated_capital=10000.0
    )
    print(f"✅ Created bot: {bot}")

    # Create signal
    signal = repo.signals.create_signal(
        bot_id=bot.id,
        symbol="BTC/USDT",
        signal_type=SignalType.BUY,
        price=50000.0,
        confidence_score=0.85,
        ml_score=0.8,
        sentiment_score=0.9,
        recommended_size=0.1
    )
    print(f"✅ Created signal: {signal}")

    # Open position
    position = repo.positions.open_position(
        bot_id=bot.id,
        user_id=user.id,
        symbol="BTC/USDT",
        side="long",
        entry_price=50050.0,
        size=0.1,
        entry_capital=5005.0,
        stop_loss=49050.0,
        take_profit=52050.0
    )
    print(f"✅ Opened position: {position}")

    # Create trade
    trade = repo.trades.create_trade(
        bot_id=bot.id,
        user_id=user.id,
        symbol="BTC/USDT",
        side="buy",
        action=TradeAction.ENTER,
        order_type="market",
        price=50050.0,
        size=0.1,
        cost=5005.0,
        exchange="binance",
        signal_id=signal.id,
        position_id=position.id
    )
    print(f"✅ Created trade: {trade}")

    # Update trade status
    repo.trades.update_trade_status(
        trade.id,
        status=OrderStatus.FILLED,
        filled_size=0.1,
        order_id="binance_order_123"
    )
    print(f"✅ Updated trade status to FILLED")

    # Log system event
    event = repo.events.log_event(
        event_type="trade_executed",
        severity="info",
        message=f"Trade executed: {trade.symbol} {trade.side} @ {trade.price}",
        user_id=user.id,
        bot_id=bot.id
    )
    print(f"✅ Logged event: {event}")

    print("\n" + "="*80)
    print("✅ Database operations complete")
    print("="*80)

    session.close()
