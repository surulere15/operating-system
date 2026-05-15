"""
Trading Competitions & Leaderboards
Gamification and community engagement through competitive trading

Premium feature worth $30-50/month on competitor platforms
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Session
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
import enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base = declarative_base()


class CompetitionStatus(str, enum.Enum):
    UPCOMING = "upcoming"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Competition(Base):
    """Trading competition"""
    __tablename__ = "competitions"

    id = Column(Integer, primary_key=True, index=True)

    # Competition details
    name = Column(String, nullable=False)
    description = Column(Text)
    rules = Column(Text)

    # Timing
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    status = Column(Enum(CompetitionStatus), default=CompetitionStatus.UPCOMING)

    # Entry requirements
    entry_fee = Column(Float, default=0)  # USDT
    min_balance = Column(Float, default=100)
    max_participants = Column(Integer)

    # Prize pool
    total_prize_pool = Column(Float, default=0)
    first_prize = Column(Float, default=0)
    second_prize = Column(Float, default=0)
    third_prize = Column(Float, default=0)

    # Competition settings
    allowed_symbols = Column(Text)  # JSON list
    max_leverage = Column(Integer, default=10)
    virtual_balance = Column(Float, default=10000)  # Starting balance for all

    # Metadata
    total_participants = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CompetitionEntry(Base):
    """User entry in a competition"""
    __tablename__ = "competition_entries"

    id = Column(Integer, primary_key=True, index=True)
    competition_id = Column(Integer, ForeignKey("competitions.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Performance tracking
    starting_balance = Column(Float, nullable=False)
    current_balance = Column(Float, nullable=False)
    total_pnl = Column(Float, default=0)
    total_pnl_percent = Column(Float, default=0)
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    win_rate = Column(Float, default=0)

    # Risk metrics
    max_drawdown = Column(Float, default=0)
    sharpe_ratio = Column(Float, default=0)

    # Ranking
    current_rank = Column(Integer)
    best_rank = Column(Integer)

    # Prizes
    prize_won = Column(Float, default=0)
    prize_paid = Column(Boolean, default=False)

    # Timestamps
    joined_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CompetitionManager:
    """
    Manages trading competitions and leaderboards

    Features:
    - Create and manage competitions
    - Track participant performance
    - Real-time leaderboards
    - Prize distribution
    - Historical statistics
    """

    def __init__(self, db: Session):
        self.db = db

    def create_competition(self, competition_data: Dict) -> Competition:
        """
        Create a new trading competition

        Args:
            competition_data: Dict with competition details

        Returns:
            Created Competition object
        """
        try:
            competition = Competition(
                name=competition_data['name'],
                description=competition_data.get('description', ''),
                rules=competition_data.get('rules', ''),
                start_date=competition_data['start_date'],
                end_date=competition_data['end_date'],
                entry_fee=competition_data.get('entry_fee', 0),
                min_balance=competition_data.get('min_balance', 100),
                max_participants=competition_data.get('max_participants'),
                total_prize_pool=competition_data.get('total_prize_pool', 0),
                first_prize=competition_data.get('first_prize', 0),
                second_prize=competition_data.get('second_prize', 0),
                third_prize=competition_data.get('third_prize', 0),
                virtual_balance=competition_data.get('virtual_balance', 10000),
                max_leverage=competition_data.get('max_leverage', 10)
            )

            self.db.add(competition)
            self.db.commit()
            self.db.refresh(competition)

            logger.info(f"✅ Competition created: {competition.name}")
            return competition

        except Exception as e:
            logger.error(f"❌ Competition creation failed: {str(e)}")
            self.db.rollback()
            raise

    def join_competition(self, competition_id: int, user_id: int) -> Optional[CompetitionEntry]:
        """
        User joins a competition

        Args:
            competition_id: Competition ID
            user_id: User ID

        Returns:
            CompetitionEntry if successful
        """
        try:
            # Get competition
            competition = self.db.query(Competition).filter(
                Competition.id == competition_id
            ).first()

            if not competition:
                logger.warning(f"⚠️ Competition not found: {competition_id}")
                return None

            # Check if already joined
            existing = self.db.query(CompetitionEntry).filter(
                CompetitionEntry.competition_id == competition_id,
                CompetitionEntry.user_id == user_id
            ).first()

            if existing:
                logger.warning(f"⚠️ User {user_id} already in competition {competition_id}")
                return existing

            # Check if competition is open
            if competition.status != CompetitionStatus.ACTIVE:
                logger.warning(f"⚠️ Competition {competition_id} not active")
                return None

            # Check max participants
            if competition.max_participants:
                if competition.total_participants >= competition.max_participants:
                    logger.warning(f"⚠️ Competition {competition_id} is full")
                    return None

            # Create entry
            entry = CompetitionEntry(
                competition_id=competition_id,
                user_id=user_id,
                starting_balance=competition.virtual_balance,
                current_balance=competition.virtual_balance
            )

            self.db.add(entry)

            # Update competition participant count
            competition.total_participants += 1

            self.db.commit()
            self.db.refresh(entry)

            logger.info(f"✅ User {user_id} joined competition {competition_id}")
            return entry

        except Exception as e:
            logger.error(f"❌ Join competition failed: {str(e)}")
            self.db.rollback()
            return None

    def get_leaderboard(self, competition_id: int, limit: int = 100) -> List[Dict]:
        """
        Get competition leaderboard

        Args:
            competition_id: Competition ID
            limit: Number of entries to return

        Returns:
            List of leaderboard entries
        """
        try:
            entries = self.db.query(CompetitionEntry).filter(
                CompetitionEntry.competition_id == competition_id
            ).order_by(
                CompetitionEntry.total_pnl_percent.desc()
            ).limit(limit).all()

            # Update ranks
            for rank, entry in enumerate(entries, 1):
                entry.current_rank = rank
                if not entry.best_rank or rank < entry.best_rank:
                    entry.best_rank = rank

            self.db.commit()

            # Convert to dict
            leaderboard = []
            for entry in entries:
                from database import User
                user = self.db.query(User).filter(User.id == entry.user_id).first()

                leaderboard.append({
                    'rank': entry.current_rank,
                    'user_id': entry.user_id,
                    'username': user.full_name if user else f"User {entry.user_id}",
                    'current_balance': round(entry.current_balance, 2),
                    'total_pnl': round(entry.total_pnl, 2),
                    'total_pnl_percent': round(entry.total_pnl_percent, 2),
                    'total_trades': entry.total_trades,
                    'win_rate': round(entry.win_rate, 2),
                    'sharpe_ratio': round(entry.sharpe_ratio, 2),
                    'max_drawdown': round(entry.max_drawdown, 2)
                })

            return leaderboard

        except Exception as e:
            logger.error(f"❌ Get leaderboard failed: {str(e)}")
            return []

    def update_participant_stats(self, competition_id: int, user_id: int) -> bool:
        """
        Update participant statistics based on their trades

        Args:
            competition_id: Competition ID
            user_id: User ID

        Returns:
            True if successful
        """
        try:
            from database import Trade

            entry = self.db.query(CompetitionEntry).filter(
                CompetitionEntry.competition_id == competition_id,
                CompetitionEntry.user_id == user_id
            ).first()

            if not entry:
                return False

            competition = self.db.query(Competition).filter(
                Competition.id == competition_id
            ).first()

            # Get trades during competition period
            trades = self.db.query(Trade).filter(
                Trade.user_id == user_id,
                Trade.closed_at >= competition.start_date,
                Trade.closed_at <= competition.end_date,
                Trade.status == 'closed'
            ).all()

            # Calculate stats
            total_pnl = sum(t.pnl or 0 for t in trades)
            total_trades = len(trades)
            winning_trades = len([t for t in trades if (t.pnl or 0) > 0])
            losing_trades = len([t for t in trades if (t.pnl or 0) <= 0])

            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

            # Update entry
            entry.current_balance = entry.starting_balance + total_pnl
            entry.total_pnl = total_pnl
            entry.total_pnl_percent = (total_pnl / entry.starting_balance * 100) if entry.starting_balance > 0 else 0
            entry.total_trades = total_trades
            entry.winning_trades = winning_trades
            entry.losing_trades = losing_trades
            entry.win_rate = win_rate
            entry.updated_at = datetime.utcnow()

            self.db.commit()

            logger.info(f"✅ Updated stats for user {user_id} in competition {competition_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Update participant stats failed: {str(e)}")
            self.db.rollback()
            return False

    def end_competition(self, competition_id: int) -> Dict:
        """
        End a competition and distribute prizes

        Args:
            competition_id: Competition ID

        Returns:
            Competition results
        """
        try:
            competition = self.db.query(Competition).filter(
                Competition.id == competition_id
            ).first()

            if not competition:
                return {'success': False, 'error': 'Competition not found'}

            # Mark as completed
            competition.status = CompetitionStatus.COMPLETED
            competition.updated_at = datetime.utcnow()

            # Get final leaderboard
            leaderboard = self.get_leaderboard(competition_id, limit=3)

            # Distribute prizes
            prizes_distributed = []

            if len(leaderboard) > 0 and competition.first_prize > 0:
                # First place
                first_entry = self.db.query(CompetitionEntry).filter(
                    CompetitionEntry.competition_id == competition_id,
                    CompetitionEntry.current_rank == 1
                ).first()

                if first_entry:
                    first_entry.prize_won = competition.first_prize
                    prizes_distributed.append({
                        'rank': 1,
                        'user_id': first_entry.user_id,
                        'prize': competition.first_prize
                    })

            if len(leaderboard) > 1 and competition.second_prize > 0:
                # Second place
                second_entry = self.db.query(CompetitionEntry).filter(
                    CompetitionEntry.competition_id == competition_id,
                    CompetitionEntry.current_rank == 2
                ).first()

                if second_entry:
                    second_entry.prize_won = competition.second_prize
                    prizes_distributed.append({
                        'rank': 2,
                        'user_id': second_entry.user_id,
                        'prize': competition.second_prize
                    })

            if len(leaderboard) > 2 and competition.third_prize > 0:
                # Third place
                third_entry = self.db.query(CompetitionEntry).filter(
                    CompetitionEntry.competition_id == competition_id,
                    CompetitionEntry.current_rank == 3
                ).first()

                if third_entry:
                    third_entry.prize_won = competition.third_prize
                    prizes_distributed.append({
                        'rank': 3,
                        'user_id': third_entry.user_id,
                        'prize': competition.third_prize
                    })

            self.db.commit()

            logger.info(f"✅ Competition {competition_id} ended. Prizes distributed: {len(prizes_distributed)}")

            return {
                'success': True,
                'competition_id': competition_id,
                'total_participants': competition.total_participants,
                'leaderboard': leaderboard,
                'prizes_distributed': prizes_distributed
            }

        except Exception as e:
            logger.error(f"❌ End competition failed: {str(e)}")
            self.db.rollback()
            return {'success': False, 'error': str(e)}

    def get_active_competitions(self) -> List[Competition]:
        """Get all active competitions"""
        return self.db.query(Competition).filter(
            Competition.status == CompetitionStatus.ACTIVE
        ).order_by(Competition.start_date.desc()).all()

    def get_upcoming_competitions(self) -> List[Competition]:
        """Get upcoming competitions"""
        return self.db.query(Competition).filter(
            Competition.status == CompetitionStatus.UPCOMING
        ).order_by(Competition.start_date.asc()).all()

    def get_user_competitions(self, user_id: int) -> List[Dict]:
        """Get competitions user has joined"""
        entries = self.db.query(CompetitionEntry).filter(
            CompetitionEntry.user_id == user_id
        ).all()

        result = []
        for entry in entries:
            competition = self.db.query(Competition).filter(
                Competition.id == entry.competition_id
            ).first()

            if competition:
                result.append({
                    'competition': {
                        'id': competition.id,
                        'name': competition.name,
                        'status': competition.status.value,
                        'start_date': competition.start_date.isoformat(),
                        'end_date': competition.end_date.isoformat()
                    },
                    'entry': {
                        'current_rank': entry.current_rank,
                        'total_pnl_percent': round(entry.total_pnl_percent, 2),
                        'prize_won': entry.prize_won
                    }
                })

        return result


def create_competition_tables(engine):
    """Create competition tables in database"""
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Competition tables created")
