"""
Social Trading / Copy Trading System
Allow users to copy successful traders automatically

This is a PREMIUM feature worth $99+/month on competitor platforms
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import List, Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base = declarative_base()


# ============================================================================
# DATABASE MODELS FOR SOCIAL TRADING
# ============================================================================

class TraderProfile(Base):
    """Public trader profile for social trading"""
    __tablename__ = "trader_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    # Public profile
    display_name = Column(String, nullable=False)
    bio = Column(Text)
    avatar_url = Column(String)

    # Privacy settings
    is_public = Column(Boolean, default=False)  # Can be copied
    allow_copying = Column(Boolean, default=False)

    # Performance stats (cached for leaderboard)
    total_followers = Column(Integer, default=0)
    total_pnl = Column(Float, default=0)
    win_rate = Column(Float, default=0)
    total_trades = Column(Integer, default=0)
    avg_roi = Column(Float, default=0)  # Average return on investment
    sharpe_ratio = Column(Float, default=0)
    max_drawdown = Column(Float, default=0)

    # Trading stats
    best_trade = Column(Float, default=0)
    worst_trade = Column(Float, default=0)
    avg_trade_duration_hours = Column(Float, default=0)

    # Reputation
    rating = Column(Float, default=0)  # 0-5 stars
    total_ratings = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_trade_at = Column(DateTime)

    # Relationships
    # followers = relationship("CopyRelationship", foreign_keys="CopyRelationship.trader_id", back_populates="trader")


class CopyRelationship(Base):
    """User following/copying another trader"""
    __tablename__ = "copy_relationships"

    id = Column(Integer, primary_key=True, index=True)

    # Who is copying whom
    follower_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    trader_id = Column(Integer, ForeignKey("trader_profiles.id"), nullable=False)

    # Copy settings
    is_active = Column(Boolean, default=True)
    copy_amount = Column(Float, default=100)  # Amount to allocate for copying
    copy_multiplier = Column(Float, default=1.0)  # 1.0 = same size, 0.5 = half size, 2.0 = double
    max_daily_loss = Column(Float, default=10)  # Stop copying if daily loss exceeds this %

    # Statistics
    total_copied_trades = Column(Integer, default=0)
    total_pnl = Column(Float, default=0)

    # Timestamps
    started_at = Column(DateTime, default=datetime.utcnow)
    stopped_at = Column(DateTime)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    # trader = relationship("TraderProfile", foreign_keys=[trader_id], back_populates="followers")


class TraderRating(Base):
    """User ratings for traders"""
    __tablename__ = "trader_ratings"

    id = Column(Integer, primary_key=True, index=True)
    trader_id = Column(Integer, ForeignKey("trader_profiles.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    rating = Column(Integer, nullable=False)  # 1-5 stars
    comment = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============================================================================
# SOCIAL TRADING ENGINE
# ============================================================================

class SocialTradingEngine:
    """
    Copy trading engine that replicates trades from successful traders

    Features:
    - Automatic trade replication
    - Position sizing based on copy multiplier
    - Risk management per copy relationship
    - Performance tracking
    """

    def __init__(self, db_session):
        self.db = db_session

    def copy_trade(self, original_trade: Dict, copy_relationship_id: int) -> Optional[Dict]:
        """
        Copy a trade from a trader to a follower

        Args:
            original_trade: The trade to copy (from trader)
            copy_relationship_id: The copy relationship ID

        Returns:
            Copied trade dict if successful
        """
        try:
            from database import Trade, User, Bot

            # Get copy relationship
            copy_rel = self.db.query(CopyRelationship).filter(
                CopyRelationship.id == copy_relationship_id
            ).first()

            if not copy_rel or not copy_rel.is_active:
                return None

            # Check daily loss limit
            if not self._check_copy_limits(copy_rel):
                logger.warning(f"⚠️ Copy limits exceeded for relationship {copy_relationship_id}")
                return None

            # Get follower's bot (create if doesn't exist)
            follower_bot = self._get_or_create_copy_bot(copy_rel.follower_id, copy_rel.trader_id)

            if not follower_bot:
                return None

            # Calculate copied position size
            original_quantity = original_trade['quantity']
            copied_quantity = original_quantity * copy_rel.copy_multiplier

            # Adjust for available capital
            follower = self.db.query(User).filter(User.id == copy_rel.follower_id).first()
            if copied_quantity * original_trade['entry_price'] > copy_rel.copy_amount:
                # Scale down to fit budget
                copied_quantity = copy_rel.copy_amount / original_trade['entry_price']

            # Create copied trade
            copied_trade = Trade(
                user_id=copy_rel.follower_id,
                bot_id=follower_bot.id,
                symbol=original_trade['symbol'],
                side=original_trade['side'],
                entry_price=original_trade['entry_price'],
                quantity=copied_quantity,
                leverage=original_trade.get('leverage', 1),
                stop_loss=original_trade.get('stop_loss'),
                take_profit=original_trade.get('take_profit'),
                status='open',
                opened_at=datetime.utcnow()
            )

            self.db.add(copied_trade)

            # Update copy relationship stats
            copy_rel.total_copied_trades += 1
            copy_rel.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(copied_trade)

            logger.info(f"✅ Copied trade: {original_trade['symbol']} for user {copy_rel.follower_id}")

            return {
                'id': copied_trade.id,
                'symbol': copied_trade.symbol,
                'side': copied_trade.side,
                'quantity': copied_trade.quantity,
                'entry_price': copied_trade.entry_price
            }

        except Exception as e:
            logger.error(f"❌ Copy trade failed: {str(e)}")
            self.db.rollback()
            return None

    def _check_copy_limits(self, copy_rel: CopyRelationship) -> bool:
        """Check if copy relationship is within risk limits"""
        try:
            from database import Trade

            # Get today's copied trades
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

            today_trades = self.db.query(Trade).join(
                CopyRelationship,
                Trade.user_id == CopyRelationship.follower_id
            ).filter(
                CopyRelationship.id == copy_rel.id,
                Trade.opened_at >= today_start,
                Trade.status == 'closed'
            ).all()

            # Calculate today's P&L
            today_pnl = sum(t.pnl or 0 for t in today_trades)
            today_pnl_percent = (today_pnl / copy_rel.copy_amount) * 100 if copy_rel.copy_amount > 0 else 0

            # Check max daily loss
            if today_pnl_percent <= -copy_rel.max_daily_loss:
                logger.warning(f"⚠️ Daily loss limit hit for copy relationship {copy_rel.id}")
                return False

            return True

        except Exception as e:
            logger.error(f"❌ Copy limits check failed: {str(e)}")
            return False

    def _get_or_create_copy_bot(self, follower_id: int, trader_id: int):
        """Get or create a bot for copying a specific trader"""
        try:
            from database import Bot, User

            # Look for existing copy bot
            bot = self.db.query(Bot).filter(
                Bot.user_id == follower_id,
                Bot.name.like(f"%Copy of Trader #{trader_id}%")
            ).first()

            if not bot:
                # Create new copy bot
                trader_profile = self.db.query(TraderProfile).filter(
                    TraderProfile.id == trader_id
                ).first()

                bot_name = f"Copy of {trader_profile.display_name if trader_profile else f'Trader #{trader_id}'}"

                bot = Bot(
                    user_id=follower_id,
                    name=bot_name,
                    exchange='bybit',  # Default exchange
                    capital=100,  # Will be updated
                    status='active',
                    config={'is_copy_bot': True, 'copying_trader_id': trader_id}
                )

                self.db.add(bot)
                self.db.commit()
                self.db.refresh(bot)

                logger.info(f"✅ Created copy bot for user {follower_id} -> trader {trader_id}")

            return bot

        except Exception as e:
            logger.error(f"❌ Get/create copy bot failed: {str(e)}")
            self.db.rollback()
            return None

    def update_trader_stats(self, user_id: int):
        """Update cached statistics for a trader profile"""
        try:
            from database import Trade

            trader_profile = self.db.query(TraderProfile).filter(
                TraderProfile.user_id == user_id
            ).first()

            if not trader_profile:
                return

            # Get all trader's closed trades
            trades = self.db.query(Trade).filter(
                Trade.user_id == user_id,
                Trade.status == 'closed'
            ).all()

            if not trades:
                return

            # Calculate stats
            total_trades = len(trades)
            winning_trades = [t for t in trades if (t.pnl or 0) > 0]
            total_pnl = sum(t.pnl or 0 for t in trades)

            win_rate = (len(winning_trades) / total_trades * 100) if total_trades > 0 else 0
            best_trade = max((t.pnl or 0) for t in trades)
            worst_trade = min((t.pnl or 0) for t in trades)

            # Average ROI
            avg_roi = (total_pnl / trader_profile.total_followers if trader_profile.total_followers > 0 else total_pnl)

            # Update trader profile
            trader_profile.total_trades = total_trades
            trader_profile.total_pnl = total_pnl
            trader_profile.win_rate = win_rate
            trader_profile.best_trade = best_trade
            trader_profile.worst_trade = worst_trade
            trader_profile.avg_roi = avg_roi
            trader_profile.updated_at = datetime.utcnow()
            trader_profile.last_trade_at = max(t.closed_at for t in trades if t.closed_at)

            self.db.commit()

            logger.info(f"✅ Updated trader stats for user {user_id}")

        except Exception as e:
            logger.error(f"❌ Update trader stats failed: {str(e)}")
            self.db.rollback()

    def get_leaderboard(self, limit: int = 50, sort_by: str = 'total_pnl') -> List[Dict]:
        """
        Get top traders leaderboard

        Args:
            limit: Number of traders to return
            sort_by: Sort field ('total_pnl', 'win_rate', 'sharpe_ratio', 'total_followers')

        Returns:
            List of trader profiles
        """
        try:
            # Build query
            query = self.db.query(TraderProfile).filter(
                TraderProfile.is_public == True,
                TraderProfile.allow_copying == True,
                TraderProfile.total_trades >= 10  # Minimum trades to appear
            )

            # Sort
            if sort_by == 'total_pnl':
                query = query.order_by(TraderProfile.total_pnl.desc())
            elif sort_by == 'win_rate':
                query = query.order_by(TraderProfile.win_rate.desc())
            elif sort_by == 'sharpe_ratio':
                query = query.order_by(TraderProfile.sharpe_ratio.desc())
            elif sort_by == 'total_followers':
                query = query.order_by(TraderProfile.total_followers.desc())
            else:
                query = query.order_by(TraderProfile.total_pnl.desc())

            traders = query.limit(limit).all()

            # Convert to dict
            leaderboard = []
            for trader in traders:
                leaderboard.append({
                    'id': trader.id,
                    'display_name': trader.display_name,
                    'bio': trader.bio,
                    'avatar_url': trader.avatar_url,
                    'total_pnl': trader.total_pnl,
                    'win_rate': trader.win_rate,
                    'total_trades': trader.total_trades,
                    'total_followers': trader.total_followers,
                    'avg_roi': trader.avg_roi,
                    'sharpe_ratio': trader.sharpe_ratio,
                    'rating': trader.rating,
                    'last_trade_at': trader.last_trade_at.isoformat() if trader.last_trade_at else None
                })

            return leaderboard

        except Exception as e:
            logger.error(f"❌ Get leaderboard failed: {str(e)}")
            return []


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def create_social_trading_tables(engine):
    """Create social trading tables in database"""
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Social trading tables created")
