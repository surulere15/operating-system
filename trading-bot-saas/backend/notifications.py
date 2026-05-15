"""
Notification System
Send alerts via Email (SendGrid) and Telegram when trades execute
"""

import os
import logging
from typing import Dict, Optional
from datetime import datetime
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
SENDGRID_FROM_EMAIL = os.getenv("SENDGRID_FROM_EMAIL", "noreply@tradingbot.com")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


class NotificationService:
    """
    Unified notification service for email and Telegram alerts

    Supports:
    - Trade executed (entry)
    - Trade closed (exit)
    - Daily summary
    - Risk alerts
    """

    @staticmethod
    def send_email(to_email: str, subject: str, html_content: str) -> bool:
        """
        Send email via SendGrid

        Args:
            to_email: Recipient email
            subject: Email subject
            html_content: HTML email body

        Returns:
            True if sent successfully
        """
        if not SENDGRID_API_KEY:
            logger.warning("⚠️ SendGrid API key not configured")
            return False

        try:
            import sendgrid
            from sendgrid.helpers.mail import Mail, Email, To, Content

            sg = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)

            message = Mail(
                from_email=Email(SENDGRID_FROM_EMAIL),
                to_emails=To(to_email),
                subject=subject,
                html_content=Content("text/html", html_content)
            )

            response = sg.send(message)

            if response.status_code in [200, 201, 202]:
                logger.info(f"✅ Email sent to {to_email}: {subject}")
                return True
            else:
                logger.error(f"❌ Email failed: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"❌ Email error: {str(e)}")
            return False

    @staticmethod
    def send_telegram(chat_id: str, message: str) -> bool:
        """
        Send Telegram message

        Args:
            chat_id: Telegram chat ID
            message: Message text (supports Markdown)

        Returns:
            True if sent successfully
        """
        if not TELEGRAM_BOT_TOKEN:
            logger.warning("⚠️ Telegram bot token not configured")
            return False

        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

            payload = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "Markdown"
            }

            response = requests.post(url, json=payload, timeout=10)

            if response.status_code == 200:
                logger.info(f"✅ Telegram sent to {chat_id}")
                return True
            else:
                logger.error(f"❌ Telegram failed: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"❌ Telegram error: {str(e)}")
            return False


class TradeNotifications:
    """Generate notification content for trade events"""

    @staticmethod
    def format_currency(value: float) -> str:
        """Format currency with proper sign"""
        return f"${abs(value):,.2f}" if value else "$0.00"

    @staticmethod
    def format_percent(value: float) -> str:
        """Format percentage with sign"""
        sign = "+" if value >= 0 else ""
        return f"{sign}{value:.2f}%"

    @staticmethod
    def trade_opened_email(user_name: str, bot_name: str, trade: Dict) -> str:
        """Generate HTML email for trade opened"""
        emoji = "🟢" if trade['side'] == 'buy' else "🔴"

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; padding: 30px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; text-align: center; }}
                .content {{ padding: 20px 0; }}
                .trade-info {{ background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 15px 0; }}
                .label {{ color: #6c757d; font-size: 12px; text-transform: uppercase; }}
                .value {{ font-size: 18px; font-weight: bold; margin-top: 5px; }}
                .footer {{ text-align: center; color: #6c757d; font-size: 12px; margin-top: 30px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{emoji} Trade Opened!</h1>
                    <p>Your bot just entered a new position</p>
                </div>

                <div class="content">
                    <p>Hi {user_name},</p>
                    <p>Your trading bot <strong>{bot_name}</strong> has opened a new {trade['side'].upper()} position.</p>

                    <div class="trade-info">
                        <div class="label">Symbol</div>
                        <div class="value">{trade.get('symbol', 'N/A')}</div>
                    </div>

                    <div class="trade-info">
                        <div class="label">Entry Price</div>
                        <div class="value">{TradeNotifications.format_currency(trade.get('entry_price', 0))}</div>
                    </div>

                    <div class="trade-info">
                        <div class="label">Quantity</div>
                        <div class="value">{trade.get('quantity', 0):.4f}</div>
                    </div>

                    <div class="trade-info">
                        <div class="label">Leverage</div>
                        <div class="value">{trade.get('leverage', 1)}x</div>
                    </div>

                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 15px;">
                        <div class="trade-info">
                            <div class="label">Stop Loss</div>
                            <div class="value" style="color: #dc3545;">{TradeNotifications.format_currency(trade.get('stop_loss', 0))}</div>
                        </div>
                        <div class="trade-info">
                            <div class="label">Take Profit</div>
                            <div class="value" style="color: #28a745;">{TradeNotifications.format_currency(trade.get('take_profit', 0))}</div>
                        </div>
                    </div>

                    <p style="margin-top: 20px;">
                        <a href="https://yourapp.com/dashboard/trades" style="background: #667eea; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">
                            View Trade Details
                        </a>
                    </p>
                </div>

                <div class="footer">
                    <p>Trading Bot SaaS • Automated Trading Platform</p>
                    <p>To unsubscribe, update your notification preferences in your dashboard.</p>
                </div>
            </div>
        </body>
        </html>
        """
        return html

    @staticmethod
    def trade_opened_telegram(bot_name: str, trade: Dict) -> str:
        """Generate Telegram message for trade opened"""
        emoji = "🟢" if trade['side'] == 'buy' else "🔴"

        message = f"""
{emoji} *Trade Opened!*

*Bot:* {bot_name}
*Symbol:* {trade.get('symbol', 'N/A')}
*Side:* {trade['side'].upper()}
*Entry:* {TradeNotifications.format_currency(trade.get('entry_price', 0))}
*Quantity:* {trade.get('quantity', 0):.4f}
*Leverage:* {trade.get('leverage', 1)}x

📉 *Stop Loss:* {TradeNotifications.format_currency(trade.get('stop_loss', 0))}
📈 *Take Profit:* {TradeNotifications.format_currency(trade.get('take_profit', 0))}

_View your dashboard for details_
        """
        return message.strip()

    @staticmethod
    def trade_closed_email(user_name: str, bot_name: str, trade: Dict) -> str:
        """Generate HTML email for trade closed"""
        pnl = trade.get('pnl', 0)
        pnl_percent = trade.get('pnl_percent', 0)
        is_profit = pnl >= 0
        emoji = "✅" if is_profit else "❌"
        color = "#28a745" if is_profit else "#dc3545"

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; padding: 30px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; text-align: center; }}
                .content {{ padding: 20px 0; }}
                .trade-info {{ background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 15px 0; }}
                .pnl-box {{ background: {color}; color: white; padding: 20px; border-radius: 8px; text-align: center; margin: 20px 0; }}
                .label {{ color: #6c757d; font-size: 12px; text-transform: uppercase; }}
                .value {{ font-size: 18px; font-weight: bold; margin-top: 5px; }}
                .footer {{ text-align: center; color: #6c757d; font-size: 12px; margin-top: 30px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{emoji} Trade Closed!</h1>
                    <p>Your position has been closed</p>
                </div>

                <div class="content">
                    <p>Hi {user_name},</p>
                    <p>Your trading bot <strong>{bot_name}</strong> has closed a {trade['side'].upper()} position.</p>

                    <div class="pnl-box">
                        <div style="font-size: 14px; opacity: 0.9;">Profit & Loss</div>
                        <div style="font-size: 32px; font-weight: bold; margin: 10px 0;">
                            {TradeNotifications.format_currency(pnl)}
                        </div>
                        <div style="font-size: 20px;">
                            {TradeNotifications.format_percent(pnl_percent)}
                        </div>
                    </div>

                    <div class="trade-info">
                        <div class="label">Symbol</div>
                        <div class="value">{trade.get('symbol', 'N/A')}</div>
                    </div>

                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                        <div class="trade-info">
                            <div class="label">Entry Price</div>
                            <div class="value">{TradeNotifications.format_currency(trade.get('entry_price', 0))}</div>
                        </div>
                        <div class="trade-info">
                            <div class="label">Exit Price</div>
                            <div class="value">{TradeNotifications.format_currency(trade.get('exit_price', 0))}</div>
                        </div>
                    </div>

                    <div class="trade-info">
                        <div class="label">Exit Reason</div>
                        <div class="value">{trade.get('exit_reason', 'manual').replace('_', ' ').title()}</div>
                    </div>

                    <p style="margin-top: 20px;">
                        <a href="https://yourapp.com/dashboard/trades" style="background: #667eea; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">
                            View All Trades
                        </a>
                    </p>
                </div>

                <div class="footer">
                    <p>Trading Bot SaaS • Automated Trading Platform</p>
                    <p>To unsubscribe, update your notification preferences in your dashboard.</p>
                </div>
            </div>
        </body>
        </html>
        """
        return html

    @staticmethod
    def trade_closed_telegram(bot_name: str, trade: Dict) -> str:
        """Generate Telegram message for trade closed"""
        pnl = trade.get('pnl', 0)
        pnl_percent = trade.get('pnl_percent', 0)
        is_profit = pnl >= 0
        emoji = "✅" if is_profit else "❌"

        message = f"""
{emoji} *Trade Closed!*

*Bot:* {bot_name}
*Symbol:* {trade.get('symbol', 'N/A')}

*P&L:* {TradeNotifications.format_currency(pnl)} ({TradeNotifications.format_percent(pnl_percent)})

*Entry:* {TradeNotifications.format_currency(trade.get('entry_price', 0))}
*Exit:* {TradeNotifications.format_currency(trade.get('exit_price', 0))}
*Reason:* {trade.get('exit_reason', 'manual').replace('_', ' ').title()}

{"🎉 Great trade!" if is_profit else "💪 Better luck next time!"}
        """
        return message.strip()

    @staticmethod
    def daily_summary_email(user_name: str, stats: Dict) -> str:
        """Generate daily summary email"""
        total_pnl = stats.get('total_pnl', 0)
        is_profit = total_pnl >= 0
        color = "#28a745" if is_profit else "#dc3545"

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; padding: 30px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; text-align: center; }}
                .stat-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin: 20px 0; }}
                .stat-box {{ background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; }}
                .stat-value {{ font-size: 24px; font-weight: bold; margin-top: 5px; }}
                .footer {{ text-align: center; color: #6c757d; font-size: 12px; margin-top: 30px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📊 Daily Trading Summary</h1>
                    <p>{datetime.now().strftime("%B %d, %Y")}</p>
                </div>

                <div style="padding: 20px 0;">
                    <p>Hi {user_name},</p>
                    <p>Here's your trading summary for today:</p>

                    <div style="background: {color}; color: white; padding: 20px; border-radius: 8px; text-align: center; margin: 20px 0;">
                        <div style="font-size: 14px; opacity: 0.9;">Total P&L Today</div>
                        <div style="font-size: 32px; font-weight: bold; margin: 10px 0;">
                            {TradeNotifications.format_currency(total_pnl)}
                        </div>
                    </div>

                    <div class="stat-grid">
                        <div class="stat-box">
                            <div style="color: #6c757d; font-size: 12px;">Total Trades</div>
                            <div class="stat-value">{stats.get('total_trades', 0)}</div>
                        </div>
                        <div class="stat-box">
                            <div style="color: #6c757d; font-size: 12px;">Win Rate</div>
                            <div class="stat-value">{stats.get('win_rate', 0):.1f}%</div>
                        </div>
                        <div class="stat-box">
                            <div style="color: #6c757d; font-size: 12px;">Winning Trades</div>
                            <div class="stat-value" style="color: #28a745;">{stats.get('winning_trades', 0)}</div>
                        </div>
                        <div class="stat-box">
                            <div style="color: #6c757d; font-size: 12px;">Losing Trades</div>
                            <div class="stat-value" style="color: #dc3545;">{stats.get('losing_trades', 0)}</div>
                        </div>
                    </div>

                    <p style="margin-top: 20px;">
                        <a href="https://yourapp.com/dashboard" style="background: #667eea; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">
                            View Dashboard
                        </a>
                    </p>
                </div>

                <div class="footer">
                    <p>Trading Bot SaaS • Automated Trading Platform</p>
                </div>
            </div>
        </body>
        </html>
        """
        return html


def send_trade_notification(user_email: str, telegram_id: Optional[str],
                            user_name: str, bot_name: str, trade: Dict, event_type: str):
    """
    Send trade notification via configured channels

    Args:
        user_email: User's email address
        telegram_id: User's Telegram chat ID (optional)
        user_name: User's full name
        bot_name: Bot name
        trade: Trade data dict
        event_type: 'opened' or 'closed'
    """
    service = NotificationService()

    if event_type == 'opened':
        # Email
        subject = f"🟢 Trade Opened: {trade.get('symbol', 'N/A')} - {bot_name}"
        html = TradeNotifications.trade_opened_email(user_name, bot_name, trade)
        service.send_email(user_email, subject, html)

        # Telegram
        if telegram_id:
            message = TradeNotifications.trade_opened_telegram(bot_name, trade)
            service.send_telegram(telegram_id, message)

    elif event_type == 'closed':
        # Email
        pnl = trade.get('pnl', 0)
        emoji = "✅" if pnl >= 0 else "❌"
        subject = f"{emoji} Trade Closed: {TradeNotifications.format_currency(pnl)} P&L - {bot_name}"
        html = TradeNotifications.trade_closed_email(user_name, bot_name, trade)
        service.send_email(user_email, subject, html)

        # Telegram
        if telegram_id:
            message = TradeNotifications.trade_closed_telegram(bot_name, trade)
            service.send_telegram(telegram_id, message)
