"""
Multi-Channel Notification System
Instant alerts via Telegram, Email, SMS, and Push Notifications

Features:
- Telegram bot integration
- Email (SendGrid/AWS SES)
- SMS (Twilio)
- Push notifications (Firebase)
- Customizable alert preferences
- Alert templates
- Priority levels
- Delivery tracking

Goal: Instant notifications (<2 seconds from signal to alert)
"""

import aiohttp
import asyncio
from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# NOTIFICATION TYPES & PRIORITIES
# ============================================================================

class NotificationType(Enum):
    """Notification types"""
    SIGNAL_GENERATED = "signal_generated"
    TRADE_EXECUTED = "trade_executed"
    POSITION_OPENED = "position_opened"
    POSITION_CLOSED = "position_closed"
    STOP_LOSS_HIT = "stop_loss_hit"
    TAKE_PROFIT_HIT = "take_profit_hit"
    BOT_STARTED = "bot_started"
    BOT_STOPPED = "bot_stopped"
    DAILY_SUMMARY = "daily_summary"
    PROFIT_MILESTONE = "profit_milestone"
    LOSS_WARNING = "loss_warning"


class NotificationPriority(Enum):
    """Priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class NotificationPreferences:
    """User notification preferences"""
    user_id: str

    # Channels enabled
    telegram_enabled: bool = True
    email_enabled: bool = True
    sms_enabled: bool = False
    push_enabled: bool = True

    # Contact info
    telegram_chat_id: Optional[str] = None
    email_address: Optional[str] = None
    phone_number: Optional[str] = None
    device_tokens: List[str] = None

    # Notification types enabled
    signal_notifications: bool = True
    trade_notifications: bool = True
    position_notifications: bool = True
    bot_status_notifications: bool = True
    daily_summary: bool = True
    profit_milestones: bool = True
    loss_warnings: bool = True

    # Quiet hours
    quiet_hours_enabled: bool = False
    quiet_hours_start: int = 22  # 10 PM
    quiet_hours_end: int = 7  # 7 AM


# ============================================================================
# TELEGRAM NOTIFIER
# ============================================================================

class TelegramNotifier:
    """
    Send notifications via Telegram
    """

    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.api_url = f"https://api.telegram.org/bot{bot_token}"

    async def send_message(
        self,
        chat_id: str,
        message: str,
        parse_mode: str = "Markdown",
        reply_markup: Optional[Dict] = None
    ) -> bool:
        """
        Send Telegram message

        Args:
            chat_id: Telegram chat ID
            message: Message text
            parse_mode: Parse mode (Markdown or HTML)
            reply_markup: Optional inline keyboard

        Returns:
            Success status
        """
        url = f"{self.api_url}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': parse_mode
        }

        if reply_markup:
            payload['reply_markup'] = json.dumps(reply_markup)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        logger.info(f"✅ Telegram message sent to {chat_id}")
                        return True
                    else:
                        logger.error(f"❌ Telegram send failed: {response.status}")
                        return False

        except Exception as e:
            logger.error(f"❌ Telegram error: {str(e)}")
            return False

    def format_signal_message(self, signal_data: Dict) -> str:
        """Format signal notification"""
        emoji = "🟢" if signal_data['type'] == 'BUY' else "🔴"

        return f"""
{emoji} **LIVE TRADING SIGNAL** {emoji}

**Symbol:** {signal_data['symbol']}
**Action:** {signal_data['type']}
**Strength:** {signal_data.get('strength', 'MODERATE').upper()}

💰 **Entry:** ${signal_data['entry_price']:,.2f}
🛑 **Stop Loss:** ${signal_data.get('stop_loss', 0):,.2f}
🎯 **Take Profit:** ${signal_data.get('take_profit', 0):,.2f}

📊 **Position Size:** ${signal_data.get('position_size_usd', 0):,.0f}
📈 **Confidence:** {signal_data.get('confidence', 0)*100:.0f}%

🤖 Bot: {signal_data.get('bot_id', 'Unknown')}
⏰ {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
"""

    def format_trade_execution_message(self, trade_data: Dict) -> str:
        """Format trade execution notification"""
        status_emoji = "✅" if trade_data.get('success') else "❌"

        return f"""
{status_emoji} **TRADE EXECUTED**

**Status:** {'FILLED' if trade_data.get('success') else 'FAILED'}
**Symbol:** {trade_data['symbol']}
**Side:** {trade_data['side'].upper()}

💰 **Price:** ${trade_data.get('price', 0):,.2f}
📊 **Size:** {trade_data.get('size', 0)} {trade_data['symbol'].split('/')[0]}
💵 **Value:** ${trade_data.get('value', 0):,.0f}

📝 **Order ID:** {trade_data.get('order_id', 'N/A')}
⏰ {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
"""

    def format_pnl_update_message(self, pnl_data: Dict) -> str:
        """Format P&L update notification"""
        pnl_emoji = "📈" if pnl_data.get('total_pnl', 0) > 0 else "📉"

        return f"""
{pnl_emoji} **PROFIT & LOSS UPDATE**

**Total P&L:** ${pnl_data.get('total_pnl', 0):,.2f} ({pnl_data.get('total_pnl_percent', 0):.2f}%)
**Today's P&L:** ${pnl_data.get('today_pnl', 0):,.2f} ({pnl_data.get('today_pnl_percent', 0):.2f}%)

📊 **Open Positions:** {pnl_data.get('open_positions', 0)}
💰 **Open P&L:** ${pnl_data.get('open_pnl', 0):,.2f}

⏰ {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
"""


# ============================================================================
# EMAIL NOTIFIER
# ============================================================================

class EmailNotifier:
    """
    Send notifications via Email (SendGrid)
    """

    def __init__(self, api_key: str, from_email: str):
        self.api_key = api_key
        self.from_email = from_email
        self.api_url = "https://api.sendgrid.com/v3/mail/send"

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str
    ) -> bool:
        """
        Send email via SendGrid

        Args:
            to_email: Recipient email
            subject: Email subject
            html_content: HTML email content

        Returns:
            Success status
        """
        payload = {
            'personalizations': [{
                'to': [{'email': to_email}],
                'subject': subject
            }],
            'from': {'email': self.from_email},
            'content': [{
                'type': 'text/html',
                'value': html_content
            }]
        }

        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url, json=payload, headers=headers) as response:
                    if response.status == 202:
                        logger.info(f"✅ Email sent to {to_email}")
                        return True
                    else:
                        logger.error(f"❌ Email send failed: {response.status}")
                        return False

        except Exception as e:
            logger.error(f"❌ Email error: {str(e)}")
            return False

    def format_signal_email(self, signal_data: Dict) -> str:
        """Format signal email HTML"""
        color = "#28a745" if signal_data['type'] == 'BUY' else "#dc3545"

        return f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <div style="background-color: {color}; color: white; padding: 20px; border-radius: 5px;">
                <h2>🔔 Live Trading Signal</h2>
            </div>
            <div style="padding: 20px;">
                <h3>{signal_data['symbol']} - {signal_data['type']}</h3>
                <p><strong>Entry Price:</strong> ${signal_data['entry_price']:,.2f}</p>
                <p><strong>Stop Loss:</strong> ${signal_data.get('stop_loss', 0):,.2f}</p>
                <p><strong>Take Profit:</strong> ${signal_data.get('take_profit', 0):,.2f}</p>
                <p><strong>Confidence:</strong> {signal_data.get('confidence', 0)*100:.0f}%</p>
                <p><strong>Time:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
            </div>
        </body>
        </html>
        """


# ============================================================================
# SMS NOTIFIER
# ============================================================================

class SMSNotifier:
    """
    Send notifications via SMS (Twilio)
    """

    def __init__(self, account_sid: str, auth_token: str, from_number: str):
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.from_number = from_number
        self.api_url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"

    async def send_sms(self, to_number: str, message: str) -> bool:
        """
        Send SMS via Twilio

        Args:
            to_number: Recipient phone number (+1234567890)
            message: SMS message

        Returns:
            Success status
        """
        payload = {
            'From': self.from_number,
            'To': to_number,
            'Body': message
        }

        try:
            import aiohttp
            from aiohttp import BasicAuth

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_url,
                    data=payload,
                    auth=BasicAuth(self.account_sid, self.auth_token)
                ) as response:
                    if response.status in [200, 201]:
                        logger.info(f"✅ SMS sent to {to_number}")
                        return True
                    else:
                        logger.error(f"❌ SMS send failed: {response.status}")
                        return False

        except Exception as e:
            logger.error(f"❌ SMS error: {str(e)}")
            return False

    def format_signal_sms(self, signal_data: Dict) -> str:
        """Format signal SMS (160 char limit)"""
        return f"🔔 {signal_data['type']} {signal_data['symbol']} @ ${signal_data['entry_price']:,.0f} | Conf: {signal_data.get('confidence', 0)*100:.0f}%"


# ============================================================================
# PUSH NOTIFICATION SERVICE
# ============================================================================

class PushNotifier:
    """
    Send push notifications (Firebase Cloud Messaging)
    """

    def __init__(self, server_key: str):
        self.server_key = server_key
        self.api_url = "https://fcm.googleapis.com/fcm/send"

    async def send_push(
        self,
        device_tokens: List[str],
        title: str,
        body: str,
        data: Optional[Dict] = None
    ) -> bool:
        """
        Send push notification via FCM

        Args:
            device_tokens: List of device tokens
            title: Notification title
            body: Notification body
            data: Optional data payload

        Returns:
            Success status
        """
        payload = {
            'registration_ids': device_tokens,
            'notification': {
                'title': title,
                'body': body,
                'sound': 'default',
                'priority': 'high'
            }
        }

        if data:
            payload['data'] = data

        headers = {
            'Authorization': f'key={self.server_key}',
            'Content-Type': 'application/json'
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        logger.info(f"✅ Push notification sent to {len(device_tokens)} devices")
                        return True
                    else:
                        logger.error(f"❌ Push send failed: {response.status}")
                        return False

        except Exception as e:
            logger.error(f"❌ Push error: {str(e)}")
            return False


# ============================================================================
# UNIFIED NOTIFICATION MANAGER
# ============================================================================

class NotificationManager:
    """
    Unified notification manager for all channels
    """

    def __init__(
        self,
        telegram_token: Optional[str] = None,
        sendgrid_key: Optional[str] = None,
        sendgrid_from: Optional[str] = None,
        twilio_sid: Optional[str] = None,
        twilio_token: Optional[str] = None,
        twilio_from: Optional[str] = None,
        fcm_key: Optional[str] = None
    ):
        # Initialize notifiers
        self.telegram = TelegramNotifier(telegram_token) if telegram_token else None
        self.email = EmailNotifier(sendgrid_key, sendgrid_from) if sendgrid_key else None
        self.sms = SMSNotifier(twilio_sid, twilio_token, twilio_from) if twilio_sid else None
        self.push = PushNotifier(fcm_key) if fcm_key else None

    async def send_signal_notification(
        self,
        signal_data: Dict,
        preferences: NotificationPreferences
    ):
        """
        Send signal notification via all enabled channels

        Args:
            signal_data: Signal data
            preferences: User preferences
        """
        if not preferences.signal_notifications:
            return

        logger.info(f"📢 Sending signal notifications for {signal_data['symbol']}")

        # Send via all enabled channels simultaneously
        tasks = []

        if preferences.telegram_enabled and self.telegram and preferences.telegram_chat_id:
            message = self.telegram.format_signal_message(signal_data)
            tasks.append(
                self.telegram.send_message(preferences.telegram_chat_id, message)
            )

        if preferences.email_enabled and self.email and preferences.email_address:
            html = self.email.format_signal_email(signal_data)
            tasks.append(
                self.email.send_email(
                    preferences.email_address,
                    f"🔔 Trading Signal: {signal_data['type']} {signal_data['symbol']}",
                    html
                )
            )

        if preferences.sms_enabled and self.sms and preferences.phone_number:
            sms_text = self.sms.format_signal_sms(signal_data)
            tasks.append(
                self.sms.send_sms(preferences.phone_number, sms_text)
            )

        if preferences.push_enabled and self.push and preferences.device_tokens:
            tasks.append(
                self.push.send_push(
                    preferences.device_tokens,
                    f"🔔 Trading Signal",
                    f"{signal_data['type']} {signal_data['symbol']} @ ${signal_data['entry_price']:,.2f}",
                    data=signal_data
                )
            )

        # Send all notifications simultaneously
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            success_count = sum(1 for r in results if r is True)
            logger.info(f"✅ Sent {success_count}/{len(tasks)} notifications successfully")

    async def send_trade_notification(
        self,
        trade_data: Dict,
        preferences: NotificationPreferences
    ):
        """Send trade execution notification"""
        if not preferences.trade_notifications:
            return

        logger.info(f"📢 Sending trade notifications for {trade_data['symbol']}")

        tasks = []

        if preferences.telegram_enabled and self.telegram and preferences.telegram_chat_id:
            message = self.telegram.format_trade_execution_message(trade_data)
            tasks.append(
                self.telegram.send_message(preferences.telegram_chat_id, message)
            )

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

async def example_notifications():
    """Example notification usage"""

    print("\n" + "="*80)
    print("MULTI-CHANNEL NOTIFICATIONS - DEMO")
    print("="*80)

    # Create notification manager (demo mode - no real API keys)
    manager = NotificationManager(
        telegram_token="demo_token",
        sendgrid_key="demo_key",
        sendgrid_from="alerts@tradingbot.com"
    )

    # User preferences
    prefs = NotificationPreferences(
        user_id="user_123",
        telegram_enabled=True,
        email_enabled=True,
        telegram_chat_id="123456789",
        email_address="user@example.com"
    )

    # Send signal notification
    signal_data = {
        'symbol': 'BTC/USDT',
        'type': 'BUY',
        'entry_price': 50000,
        'stop_loss': 49000,
        'take_profit': 52000,
        'confidence': 0.85,
        'position_size_usd': 1000,
        'bot_id': 'bot_123'
    }

    print("\n📨 Sending signal notification...")
    # await manager.send_signal_notification(signal_data, prefs)
    print("✅ Notifications sent (demo mode)")


if __name__ == "__main__":
    asyncio.run(example_notifications())
