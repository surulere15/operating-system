"""
Developer API & Webhooks
Programmatic access to trading platform with webhooks for signals

Premium feature worth $50-100/month on competitor platforms
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Session
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import secrets
import hashlib
import logging
from fastapi import HTTPException, Request
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base = declarative_base()


class DeveloperAPIKey(Base):
    """API keys for developer access"""
    __tablename__ = "developer_api_keys"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # API key details
    name = Column(String, nullable=False)
    key_prefix = Column(String, nullable=False)  # First 8 chars for display
    key_hash = Column(String, nullable=False)  # SHA-256 hash of full key

    # Permissions
    can_read_data = Column(Boolean, default=True)
    can_execute_trades = Column(Boolean, default=False)
    can_manage_bots = Column(Boolean, default=False)
    can_receive_webhooks = Column(Boolean, default=True)

    # Rate limiting
    rate_limit_per_minute = Column(Integer, default=60)
    rate_limit_per_hour = Column(Integer, default=1000)

    # Usage tracking
    total_requests = Column(Integer, default=0)
    last_used_at = Column(DateTime)

    # Status
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class APIUsageLog(Base):
    """Log of API requests for analytics"""
    __tablename__ = "api_usage_logs"

    id = Column(Integer, primary_key=True, index=True)
    api_key_id = Column(Integer, ForeignKey("developer_api_keys.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Request details
    endpoint = Column(String, nullable=False)
    method = Column(String, nullable=False)
    status_code = Column(Integer, nullable=False)
    response_time_ms = Column(Float)

    # IP and user agent
    ip_address = Column(String)
    user_agent = Column(Text)

    # Timestamp
    requested_at = Column(DateTime, default=datetime.utcnow)


class Webhook(Base):
    """Webhook endpoints for receiving trade signals"""
    __tablename__ = "webhooks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Webhook details
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    secret = Column(String, nullable=False)  # For signature verification

    # Event types to listen for
    listen_trade_signals = Column(Boolean, default=True)
    listen_price_alerts = Column(Boolean, default=False)
    listen_portfolio_updates = Column(Boolean, default=False)

    # Configuration
    bot_id = Column(Integer, ForeignKey("bots.id"))  # Optional: specific bot
    retry_on_failure = Column(Boolean, default=True)
    max_retries = Column(Integer, default=3)

    # Status
    is_active = Column(Boolean, default=True)
    last_triggered_at = Column(DateTime)
    total_triggers = Column(Integer, default=0)
    total_failures = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class WebhookLog(Base):
    """Log of webhook deliveries"""
    __tablename__ = "webhook_logs"

    id = Column(Integer, primary_key=True, index=True)
    webhook_id = Column(Integer, ForeignKey("webhooks.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Request details
    event_type = Column(String, nullable=False)
    payload = Column(Text, nullable=False)

    # Response
    status_code = Column(Integer)
    response_body = Column(Text)
    success = Column(Boolean, default=False)

    # Timing
    response_time_ms = Column(Float)
    attempted_at = Column(DateTime, default=datetime.utcnow)


class DeveloperAPIManager:
    """
    Manages developer API keys and webhook integrations

    Features:
    - API key generation and management
    - Rate limiting
    - Usage tracking
    - Webhook management and delivery
    """

    def __init__(self, db: Session):
        self.db = db

    def generate_api_key(self, user_id: int, name: str, permissions: Dict) -> Tuple[DeveloperAPIKey, str]:
        """
        Generate a new API key

        Args:
            user_id: User ID
            name: API key name
            permissions: Dict with permission flags

        Returns:
            (DeveloperAPIKey, plain_key) tuple
        """
        try:
            # Generate random API key
            plain_key = f"tbsk_{secrets.token_urlsafe(32)}"

            # Hash the key for storage
            key_hash = hashlib.sha256(plain_key.encode()).hexdigest()
            key_prefix = plain_key[:12]  # First 12 chars for display

            # Create API key
            api_key = DeveloperAPIKey(
                user_id=user_id,
                name=name,
                key_prefix=key_prefix,
                key_hash=key_hash,
                can_read_data=permissions.get('can_read_data', True),
                can_execute_trades=permissions.get('can_execute_trades', False),
                can_manage_bots=permissions.get('can_manage_bots', False),
                can_receive_webhooks=permissions.get('can_receive_webhooks', True),
                rate_limit_per_minute=permissions.get('rate_limit_per_minute', 60),
                rate_limit_per_hour=permissions.get('rate_limit_per_hour', 1000),
                expires_at=permissions.get('expires_at')
            )

            self.db.add(api_key)
            self.db.commit()
            self.db.refresh(api_key)

            logger.info(f"✅ API key generated for user {user_id}: {name}")

            return api_key, plain_key

        except Exception as e:
            logger.error(f"❌ API key generation failed: {str(e)}")
            self.db.rollback()
            raise

    def verify_api_key(self, plain_key: str) -> Optional[DeveloperAPIKey]:
        """
        Verify an API key and return the API key object

        Args:
            plain_key: The plain text API key

        Returns:
            DeveloperAPIKey if valid, None otherwise
        """
        try:
            # Hash the provided key
            key_hash = hashlib.sha256(plain_key.encode()).hexdigest()

            # Look up key
            api_key = self.db.query(DeveloperAPIKey).filter(
                DeveloperAPIKey.key_hash == key_hash,
                DeveloperAPIKey.is_active == True
            ).first()

            if not api_key:
                return None

            # Check expiration
            if api_key.expires_at and datetime.utcnow() > api_key.expires_at:
                return None

            # Update last used
            api_key.last_used_at = datetime.utcnow()
            api_key.total_requests += 1
            self.db.commit()

            return api_key

        except Exception as e:
            logger.error(f"❌ API key verification failed: {str(e)}")
            return None

    def check_rate_limit(self, api_key: DeveloperAPIKey) -> Tuple[bool, str]:
        """
        Check if API key is within rate limits

        Args:
            api_key: DeveloperAPIKey object

        Returns:
            (allowed: bool, message: str)
        """
        try:
            now = datetime.utcnow()

            # Check per-minute limit
            one_minute_ago = now - timedelta(minutes=1)
            recent_requests = self.db.query(APIUsageLog).filter(
                APIUsageLog.api_key_id == api_key.id,
                APIUsageLog.requested_at >= one_minute_ago
            ).count()

            if recent_requests >= api_key.rate_limit_per_minute:
                return False, f"Rate limit exceeded: {api_key.rate_limit_per_minute} requests/minute"

            # Check per-hour limit
            one_hour_ago = now - timedelta(hours=1)
            hourly_requests = self.db.query(APIUsageLog).filter(
                APIUsageLog.api_key_id == api_key.id,
                APIUsageLog.requested_at >= one_hour_ago
            ).count()

            if hourly_requests >= api_key.rate_limit_per_hour:
                return False, f"Rate limit exceeded: {api_key.rate_limit_per_hour} requests/hour"

            return True, "OK"

        except Exception as e:
            logger.error(f"❌ Rate limit check failed: {str(e)}")
            return True, "Rate limit check bypassed"

    def log_api_request(self, api_key_id: int, user_id: int, request: Request,
                       status_code: int, response_time_ms: float):
        """Log API request for analytics"""
        try:
            log = APIUsageLog(
                api_key_id=api_key_id,
                user_id=user_id,
                endpoint=str(request.url.path),
                method=request.method,
                status_code=status_code,
                response_time_ms=response_time_ms,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get('user-agent', '')
            )

            self.db.add(log)
            self.db.commit()

        except Exception as e:
            logger.error(f"❌ API logging failed: {str(e)}")

    def create_webhook(self, user_id: int, webhook_data: Dict) -> Webhook:
        """
        Create a new webhook

        Args:
            user_id: User ID
            webhook_data: Dict with webhook configuration

        Returns:
            Created Webhook object
        """
        try:
            # Generate secret for signature verification
            secret = secrets.token_urlsafe(32)

            webhook = Webhook(
                user_id=user_id,
                name=webhook_data['name'],
                url=webhook_data['url'],
                secret=secret,
                listen_trade_signals=webhook_data.get('listen_trade_signals', True),
                listen_price_alerts=webhook_data.get('listen_price_alerts', False),
                listen_portfolio_updates=webhook_data.get('listen_portfolio_updates', False),
                bot_id=webhook_data.get('bot_id'),
                retry_on_failure=webhook_data.get('retry_on_failure', True),
                max_retries=webhook_data.get('max_retries', 3)
            )

            self.db.add(webhook)
            self.db.commit()
            self.db.refresh(webhook)

            logger.info(f"✅ Webhook created for user {user_id}: {webhook.name}")

            return webhook

        except Exception as e:
            logger.error(f"❌ Webhook creation failed: {str(e)}")
            self.db.rollback()
            raise

    def trigger_webhook(self, webhook_id: int, event_type: str, payload: Dict) -> bool:
        """
        Trigger a webhook by sending HTTP POST to configured URL

        Args:
            webhook_id: Webhook ID
            event_type: Type of event ('trade_signal', 'price_alert', etc.)
            payload: Data to send

        Returns:
            True if successful
        """
        try:
            import requests
            import hmac

            webhook = self.db.query(Webhook).filter(
                Webhook.id == webhook_id,
                Webhook.is_active == True
            ).first()

            if not webhook:
                return False

            # Prepare payload
            payload_json = json.dumps(payload)

            # Generate signature
            signature = hmac.new(
                webhook.secret.encode(),
                payload_json.encode(),
                hashlib.sha256
            ).hexdigest()

            # Send webhook
            start_time = datetime.utcnow()

            response = requests.post(
                webhook.url,
                json=payload,
                headers={
                    'X-Webhook-Signature': signature,
                    'X-Event-Type': event_type,
                    'Content-Type': 'application/json'
                },
                timeout=10
            )

            response_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

            # Log webhook delivery
            success = response.status_code in [200, 201, 202]

            log = WebhookLog(
                webhook_id=webhook.id,
                user_id=webhook.user_id,
                event_type=event_type,
                payload=payload_json,
                status_code=response.status_code,
                response_body=response.text[:1000],  # Limit size
                success=success,
                response_time_ms=response_time_ms
            )

            self.db.add(log)

            # Update webhook stats
            webhook.last_triggered_at = datetime.utcnow()
            webhook.total_triggers += 1
            if not success:
                webhook.total_failures += 1

            self.db.commit()

            if success:
                logger.info(f"✅ Webhook triggered: {webhook.name} ({event_type})")
            else:
                logger.warning(f"⚠️ Webhook failed: {webhook.name} ({response.status_code})")

            return success

        except Exception as e:
            logger.error(f"❌ Webhook trigger failed: {str(e)}")

            # Log failure
            try:
                log = WebhookLog(
                    webhook_id=webhook_id,
                    user_id=webhook.user_id if webhook else 0,
                    event_type=event_type,
                    payload=json.dumps(payload),
                    status_code=0,
                    response_body=str(e),
                    success=False
                )
                self.db.add(log)

                if webhook:
                    webhook.total_failures += 1

                self.db.commit()
            except:
                pass

            return False

    def get_user_api_keys(self, user_id: int) -> List[DeveloperAPIKey]:
        """Get all API keys for a user"""
        return self.db.query(DeveloperAPIKey).filter(
            DeveloperAPIKey.user_id == user_id
        ).order_by(DeveloperAPIKey.created_at.desc()).all()

    def get_user_webhooks(self, user_id: int) -> List[Webhook]:
        """Get all webhooks for a user"""
        return self.db.query(Webhook).filter(
            Webhook.user_id == user_id
        ).order_by(Webhook.created_at.desc()).all()

    def get_api_usage_stats(self, user_id: int, days: int = 30) -> Dict:
        """Get API usage statistics"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            # Get user's API keys
            api_keys = self.db.query(DeveloperAPIKey).filter(
                DeveloperAPIKey.user_id == user_id
            ).all()

            if not api_keys:
                return self._empty_usage_stats()

            api_key_ids = [k.id for k in api_keys]

            # Total requests
            total_requests = self.db.query(APIUsageLog).filter(
                APIUsageLog.api_key_id.in_(api_key_ids),
                APIUsageLog.requested_at >= cutoff_date
            ).count()

            # Requests by endpoint
            endpoint_stats = {}
            logs = self.db.query(APIUsageLog).filter(
                APIUsageLog.api_key_id.in_(api_key_ids),
                APIUsageLog.requested_at >= cutoff_date
            ).all()

            for log in logs:
                endpoint_stats[log.endpoint] = endpoint_stats.get(log.endpoint, 0) + 1

            # Success rate
            successful = sum(1 for log in logs if 200 <= log.status_code < 300)
            success_rate = (successful / total_requests * 100) if total_requests > 0 else 0

            # Average response time
            response_times = [log.response_time_ms for log in logs if log.response_time_ms]
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0

            return {
                'total_requests': total_requests,
                'success_rate': round(success_rate, 2),
                'avg_response_time_ms': round(avg_response_time, 2),
                'endpoint_stats': endpoint_stats,
                'period_days': days
            }

        except Exception as e:
            logger.error(f"❌ Usage stats failed: {str(e)}")
            return self._empty_usage_stats()

    def _empty_usage_stats(self) -> Dict:
        """Return empty usage stats"""
        return {
            'total_requests': 0,
            'success_rate': 0,
            'avg_response_time_ms': 0,
            'endpoint_stats': {},
            'period_days': 0
        }

    def delete_api_key(self, api_key_id: int, user_id: int) -> bool:
        """Delete an API key"""
        try:
            api_key = self.db.query(DeveloperAPIKey).filter(
                DeveloperAPIKey.id == api_key_id,
                DeveloperAPIKey.user_id == user_id
            ).first()

            if not api_key:
                return False

            self.db.delete(api_key)
            self.db.commit()

            logger.info(f"✅ API key deleted: {api_key_id}")
            return True

        except Exception as e:
            logger.error(f"❌ API key deletion failed: {str(e)}")
            self.db.rollback()
            return False

    def delete_webhook(self, webhook_id: int, user_id: int) -> bool:
        """Delete a webhook"""
        try:
            webhook = self.db.query(Webhook).filter(
                Webhook.id == webhook_id,
                Webhook.user_id == user_id
            ).first()

            if not webhook:
                return False

            self.db.delete(webhook)
            self.db.commit()

            logger.info(f"✅ Webhook deleted: {webhook_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Webhook deletion failed: {str(e)}")
            self.db.rollback()
            return False


def create_developer_api_tables(engine):
    """Create developer API tables in database"""
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Developer API tables created")
