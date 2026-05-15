"""
Custom Alerts System
Price alerts, indicator alerts, and portfolio alerts

Premium feature worth $30-50/month on competitor platforms
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Session
from datetime import datetime
from typing import List, Dict, Optional
import logging
import enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base = declarative_base()


class AlertType(str, enum.Enum):
    PRICE = "price"
    INDICATOR = "indicator"
    PORTFOLIO = "portfolio"
    TRADE = "trade"


class AlertCondition(str, enum.Enum):
    ABOVE = "above"
    BELOW = "below"
    CROSSES_ABOVE = "crosses_above"
    CROSSES_BELOW = "crosses_below"
    EQUALS = "equals"
    CHANGE_PERCENT = "change_percent"


class Alert(Base):
    """User-created price and indicator alerts"""
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Alert details
    name = Column(String, nullable=False)
    description = Column(Text)
    alert_type = Column(Enum(AlertType), nullable=False)
    is_active = Column(Boolean, default=True)

    # Price alert fields
    symbol = Column(String)  # For price alerts
    condition = Column(Enum(AlertCondition), nullable=False)
    target_value = Column(Float, nullable=False)

    # Indicator alert fields
    indicator = Column(String)  # 'rsi', 'macd', 'ma', etc.
    indicator_params = Column(Text)  # JSON string

    # Portfolio alert fields
    portfolio_metric = Column(String)  # 'total_pnl', 'drawdown', 'risk_score'

    # Notification settings
    notify_email = Column(Boolean, default=True)
    notify_telegram = Column(Boolean, default=False)
    repeat = Column(Boolean, default=False)  # Repeat or one-time

    # Tracking
    times_triggered = Column(Integer, default=0)
    last_triggered_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AlertHistory(Base):
    """History of triggered alerts"""
    __tablename__ = "alert_history"

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Integer, ForeignKey("alerts.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    triggered_at = Column(DateTime, default=datetime.utcnow)
    trigger_value = Column(Float)
    message = Column(Text)
    notified_email = Column(Boolean, default=False)
    notified_telegram = Column(Boolean, default=False)


class AlertManager:
    """
    Manages creation, monitoring, and triggering of alerts

    Features:
    - Price alerts (above/below/crossing thresholds)
    - Technical indicator alerts (RSI, MACD, etc.)
    - Portfolio alerts (P&L, drawdown, risk limits)
    - Multi-channel notifications (email, Telegram)
    """

    def __init__(self, db: Session):
        self.db = db

    def create_alert(self, user_id: int, alert_data: Dict) -> Alert:
        """
        Create a new alert

        Args:
            user_id: User ID
            alert_data: Dict with alert configuration

        Returns:
            Created Alert object
        """
        try:
            alert = Alert(
                user_id=user_id,
                name=alert_data['name'],
                description=alert_data.get('description', ''),
                alert_type=AlertType(alert_data['alert_type']),
                symbol=alert_data.get('symbol'),
                condition=AlertCondition(alert_data['condition']),
                target_value=alert_data['target_value'],
                indicator=alert_data.get('indicator'),
                indicator_params=alert_data.get('indicator_params'),
                portfolio_metric=alert_data.get('portfolio_metric'),
                notify_email=alert_data.get('notify_email', True),
                notify_telegram=alert_data.get('notify_telegram', False),
                repeat=alert_data.get('repeat', False)
            )

            self.db.add(alert)
            self.db.commit()
            self.db.refresh(alert)

            logger.info(f"✅ Alert created: {alert.name} for user {user_id}")
            return alert

        except Exception as e:
            logger.error(f"❌ Alert creation failed: {str(e)}")
            self.db.rollback()
            raise

    def check_price_alert(self, alert: Alert, current_price: float, previous_price: float = None) -> bool:
        """
        Check if price alert should trigger

        Args:
            alert: Alert object
            current_price: Current market price
            previous_price: Previous price (for crossing alerts)

        Returns:
            True if alert triggered
        """
        if alert.alert_type != AlertType.PRICE:
            return False

        triggered = False

        if alert.condition == AlertCondition.ABOVE:
            triggered = current_price > alert.target_value

        elif alert.condition == AlertCondition.BELOW:
            triggered = current_price < alert.target_value

        elif alert.condition == AlertCondition.EQUALS:
            # Within 0.1% of target
            triggered = abs(current_price - alert.target_value) / alert.target_value < 0.001

        elif alert.condition == AlertCondition.CROSSES_ABOVE:
            if previous_price:
                triggered = previous_price <= alert.target_value and current_price > alert.target_value

        elif alert.condition == AlertCondition.CROSSES_BELOW:
            if previous_price:
                triggered = previous_price >= alert.target_value and current_price < alert.target_value

        elif alert.condition == AlertCondition.CHANGE_PERCENT:
            if previous_price:
                change_percent = ((current_price - previous_price) / previous_price) * 100
                triggered = abs(change_percent) >= alert.target_value

        return triggered

    def check_indicator_alert(self, alert: Alert, indicator_values: Dict) -> bool:
        """
        Check if technical indicator alert should trigger

        Args:
            alert: Alert object
            indicator_values: Dict with current indicator values

        Returns:
            True if alert triggered
        """
        if alert.alert_type != AlertType.INDICATOR:
            return False

        if alert.indicator not in indicator_values:
            return False

        indicator_value = indicator_values[alert.indicator]

        triggered = False

        if alert.condition == AlertCondition.ABOVE:
            triggered = indicator_value > alert.target_value

        elif alert.condition == AlertCondition.BELOW:
            triggered = indicator_value < alert.target_value

        return triggered

    def check_portfolio_alert(self, alert: Alert, portfolio_metrics: Dict) -> bool:
        """
        Check if portfolio alert should trigger

        Args:
            alert: Alert object
            portfolio_metrics: Dict with current portfolio metrics

        Returns:
            True if alert triggered
        """
        if alert.alert_type != AlertType.PORTFOLIO:
            return False

        if alert.portfolio_metric not in portfolio_metrics:
            return False

        metric_value = portfolio_metrics[alert.portfolio_metric]

        triggered = False

        if alert.condition == AlertCondition.ABOVE:
            triggered = metric_value > alert.target_value

        elif alert.condition == AlertCondition.BELOW:
            triggered = metric_value < alert.target_value

        return triggered

    def trigger_alert(self, alert: Alert, trigger_value: float, message: str) -> AlertHistory:
        """
        Trigger an alert and send notifications

        Args:
            alert: Alert object
            trigger_value: Value that triggered the alert
            message: Alert message

        Returns:
            AlertHistory record
        """
        try:
            # Create history record
            history = AlertHistory(
                alert_id=alert.id,
                user_id=alert.user_id,
                trigger_value=trigger_value,
                message=message,
                notified_email=False,
                notified_telegram=False
            )

            # Send notifications
            if alert.notify_email:
                success = self._send_email_notification(alert, message)
                history.notified_email = success

            if alert.notify_telegram:
                success = self._send_telegram_notification(alert, message)
                history.notified_telegram = success

            # Update alert tracking
            alert.times_triggered += 1
            alert.last_triggered_at = datetime.utcnow()

            # Deactivate if not repeating
            if not alert.repeat:
                alert.is_active = False

            self.db.add(history)
            self.db.commit()

            logger.info(f"✅ Alert triggered: {alert.name} ({message})")
            return history

        except Exception as e:
            logger.error(f"❌ Alert trigger failed: {str(e)}")
            self.db.rollback()
            raise

    def _send_email_notification(self, alert: Alert, message: str) -> bool:
        """Send email notification for alert"""
        try:
            from database import User
            from notifications import NotificationService

            user = self.db.query(User).filter(User.id == alert.user_id).first()
            if not user or not user.email:
                return False

            subject = f"🔔 Alert Triggered: {alert.name}"
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center;">
                    <h1 style="color: white; margin: 0;">🔔 Alert Triggered</h1>
                </div>
                <div style="padding: 30px; background-color: #f7fafc;">
                    <h2 style="color: #2d3748;">{alert.name}</h2>
                    <p style="color: #4a5568; font-size: 16px;">{message}</p>

                    <div style="background-color: white; border-radius: 8px; padding: 20px; margin-top: 20px;">
                        <h3 style="color: #2d3748; margin-top: 0;">Alert Details</h3>
                        <p><strong>Type:</strong> {alert.alert_type.value.capitalize()}</p>
                        <p><strong>Symbol:</strong> {alert.symbol or 'N/A'}</p>
                        <p><strong>Condition:</strong> {alert.condition.value.replace('_', ' ').title()}</p>
                        <p><strong>Target:</strong> {alert.target_value}</p>
                        <p><strong>Triggered:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                    </div>

                    <div style="text-align: center; margin-top: 30px;">
                        <a href="http://localhost:3000/dashboard/alerts" style="display: inline-block; background-color: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; font-weight: bold;">View All Alerts</a>
                    </div>
                </div>
            </body>
            </html>
            """

            success = NotificationService.send_email(user.email, subject, html_content)
            return success

        except Exception as e:
            logger.error(f"❌ Email notification failed: {str(e)}")
            return False

    def _send_telegram_notification(self, alert: Alert, message: str) -> bool:
        """Send Telegram notification for alert"""
        try:
            from database import User
            from notifications import NotificationService

            user = self.db.query(User).filter(User.id == alert.user_id).first()
            if not user or not user.telegram_chat_id:
                return False

            telegram_message = f"""
🔔 *Alert Triggered*

*{alert.name}*
{message}

Type: {alert.alert_type.value.capitalize()}
Symbol: {alert.symbol or 'N/A'}
Condition: {alert.condition.value.replace('_', ' ').title()}
Target: {alert.target_value}

Triggered: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
            """

            success = NotificationService.send_telegram(user.telegram_chat_id, telegram_message)
            return success

        except Exception as e:
            logger.error(f"❌ Telegram notification failed: {str(e)}")
            return False

    def get_user_alerts(self, user_id: int, active_only: bool = False) -> List[Alert]:
        """Get all alerts for a user"""
        query = self.db.query(Alert).filter(Alert.user_id == user_id)

        if active_only:
            query = query.filter(Alert.is_active == True)

        return query.order_by(Alert.created_at.desc()).all()

    def get_alert_history(self, user_id: int, limit: int = 50) -> List[AlertHistory]:
        """Get alert trigger history for a user"""
        return self.db.query(AlertHistory).filter(
            AlertHistory.user_id == user_id
        ).order_by(AlertHistory.triggered_at.desc()).limit(limit).all()

    def delete_alert(self, alert_id: int, user_id: int) -> bool:
        """Delete an alert"""
        try:
            alert = self.db.query(Alert).filter(
                Alert.id == alert_id,
                Alert.user_id == user_id
            ).first()

            if not alert:
                return False

            self.db.delete(alert)
            self.db.commit()

            logger.info(f"✅ Alert deleted: {alert_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Alert deletion failed: {str(e)}")
            self.db.rollback()
            return False

    def toggle_alert(self, alert_id: int, user_id: int) -> Optional[Alert]:
        """Toggle alert active status"""
        try:
            alert = self.db.query(Alert).filter(
                Alert.id == alert_id,
                Alert.user_id == user_id
            ).first()

            if not alert:
                return None

            alert.is_active = not alert.is_active
            self.db.commit()
            self.db.refresh(alert)

            logger.info(f"✅ Alert toggled: {alert_id} -> {alert.is_active}")
            return alert

        except Exception as e:
            logger.error(f"❌ Alert toggle failed: {str(e)}")
            self.db.rollback()
            return None


def create_alert_tables(engine):
    """Create alert tables in database"""
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Alert tables created")
