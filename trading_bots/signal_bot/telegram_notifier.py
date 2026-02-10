#!/usr/bin/env python3
"""
TELEGRAM NOTIFICATION SYSTEM
Sends real-time trading alerts to your phone
"""

import os
import requests
from datetime import datetime
from typing import Dict, Optional


class TelegramNotifier:
    """Send trading notifications via Telegram"""

    def __init__(self, bot_token: Optional[str] = None, chat_id: Optional[str] = None):
        """
        Initialize Telegram notifier

        Args:
            bot_token: Telegram bot token (or set TELEGRAM_BOT_TOKEN env var)
            chat_id: Your Telegram chat ID (or set TELEGRAM_CHAT_ID env var)
        """
        self.bot_token = bot_token or os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = chat_id or os.getenv('TELEGRAM_CHAT_ID')

        if not self.bot_token or not self.chat_id:
            print("⚠️  Telegram not configured - notifications disabled")
            self.enabled = False
        else:
            self.enabled = True
            print(f"✅ Telegram notifications enabled!")

    def send_message(self, message: str, silent: bool = False) -> bool:
        """Send a message to Telegram"""
        if not self.enabled:
            return False

        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'Markdown',
                'disable_notification': silent
            }

            response = requests.post(url, json=payload, timeout=10)

            if response.status_code == 200:
                return True
            else:
                print(f"⚠️  Telegram send failed: {response.status_code}")
                return False

        except Exception as e:
            print(f"⚠️  Telegram error: {e}")
            return False

    def notify_startup(self, capital: float, exchange: str, mode: str):
        """Send bot startup notification"""
        message = f"""
🚀 *TRADING BOT STARTED*

💰 Capital: ${capital:.2f} USDT
🏦 Exchange: {exchange}
🔧 Mode: {mode}
⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Bot is now monitoring markets...
        """
        self.send_message(message.strip())

    def notify_signal(self, signal: Dict):
        """Send new trading signal notification"""
        emoji = "🟢" if signal['type'] == 'BUY' else "🔴"

        message = f"""
{emoji} *{signal['type']} SIGNAL DETECTED*

📊 *{signal['symbol']}*
💰 Entry: ${signal['price']:.4f}

🎯 *Targets:*
• TP1: ${signal['take_profit_1']:.4f} (+5%)
• TP2: ${signal['take_profit_2']:.4f} (+10%)
• TP3: ${signal['take_profit_3']:.4f} (+15%)

🛑 Stop Loss: ${signal['stop_loss']:.4f} (-5%)

📈 *Indicators:*
• RSI: {signal['indicators']['rsi']}
• Trend: {signal['indicators']['trend']}
• Volume: {signal['indicators']['volume_surge']:.1f}x

⭐ Confidence: {signal['confidence']}/100

💡 {signal['reason']}

⏰ {datetime.now().strftime('%H:%M:%S')}
        """
        self.send_message(message.strip())

    def notify_order_executed(self, symbol: str, side: str, quantity: float,
                              price: float, leverage: int, position_size: float):
        """Send order execution notification"""
        emoji = "✅" if side.upper() == 'BUY' else "⚠️"

        message = f"""
{emoji} *ORDER EXECUTED*

📊 {symbol}
🔄 {side.upper()}
📦 Quantity: {quantity:.6f}
💵 Price: ${price:.4f}

⚡ Leverage: {leverage}x
💰 Position Size: ${position_size:.2f}

⏰ {datetime.now().strftime('%H:%M:%S')}
        """
        self.send_message(message.strip())

    def notify_position_closed(self, symbol: str, entry: float, exit: float,
                               pnl: float, pnl_pct: float, reason: str):
        """Send position closed notification"""
        emoji = "💚" if pnl > 0 else "❌"

        message = f"""
{emoji} *POSITION CLOSED*

📊 {symbol}
🔵 Entry: ${entry:.4f}
🔴 Exit: ${exit:.4f}

💰 P&L: ${pnl:.2f} ({pnl_pct:+.2f}%)
📝 Reason: {reason}

⏰ {datetime.now().strftime('%H:%M:%S')}
        """
        self.send_message(message.strip())

    def notify_take_profit_hit(self, symbol: str, tp_level: int, price: float, profit: float):
        """Send take profit hit notification"""
        message = f"""
🎯 *TAKE PROFIT {tp_level} HIT!*

📊 {symbol}
💰 Price: ${price:.4f}
✅ Profit: ${profit:.2f}

Partial position closed.

⏰ {datetime.now().strftime('%H:%M:%S')}
        """
        self.send_message(message.strip())

    def notify_stop_loss_hit(self, symbol: str, entry: float, exit: float, loss: float):
        """Send stop loss hit notification"""
        message = f"""
🛑 *STOP LOSS TRIGGERED*

📊 {symbol}
🔵 Entry: ${entry:.4f}
🔴 Exit: ${exit:.4f}
💸 Loss: ${loss:.2f}

Position closed to protect capital.

⏰ {datetime.now().strftime('%H:%M:%S')}
        """
        self.send_message(message.strip())

    def notify_daily_summary(self, stats: Dict):
        """Send daily trading summary"""
        total_pnl = stats.get('total_pnl', 0)
        emoji = "📈" if total_pnl > 0 else "📉"

        message = f"""
{emoji} *DAILY SUMMARY*

📊 *Trading Stats:*
• Signals: {stats.get('total_signals', 0)}
• Executed: {stats.get('signals_executed', 0)}
• Skipped: {stats.get('signals_skipped', 0)}

🎯 *Performance:*
• Wins: {stats.get('wins', 0)}
• Losses: {stats.get('losses', 0)}
• Win Rate: {stats.get('wins', 0) / max(stats.get('signals_executed', 1), 1) * 100:.1f}%

💰 *Profit & Loss:*
• Total P&L: ${total_pnl:.2f}
• ROI: {stats.get('roi', 0):.2f}%

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        self.send_message(message.strip())

    def notify_risk_alert(self, alert_type: str, message: str):
        """Send risk management alert"""
        notification = f"""
🚨 *RISK ALERT*

⚠️ {alert_type}

{message}

⏰ {datetime.now().strftime('%H:%M:%S')}
        """
        self.send_message(notification.strip())

    def notify_balance_update(self, balance: float, available: float, pnl: float):
        """Send balance update"""
        emoji = "💚" if pnl >= 0 else "❌"

        message = f"""
💼 *BALANCE UPDATE*

💰 Total: ${balance:.2f} USDT
📊 Available: ${available:.2f} USDT
{emoji} Unrealized P&L: ${pnl:.2f}

⏰ {datetime.now().strftime('%H:%M:%S')}
        """
        self.send_message(message.strip(), silent=True)

    def test_connection(self) -> bool:
        """Test Telegram connection"""
        if not self.enabled:
            print("❌ Telegram not configured")
            return False

        message = """
✅ *TELEGRAM TEST*

Your trading bot is connected!

You'll receive notifications for:
• 🎯 New signals
• ✅ Orders executed
• 💰 Positions closed
• 📊 Daily summaries
• 🚨 Risk alerts

⏰ """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        if self.send_message(message.strip()):
            print("✅ Telegram test successful!")
            return True
        else:
            print("❌ Telegram test failed")
            return False


def setup_telegram():
    """Interactive setup for Telegram notifications"""
    print("\n" + "="*60)
    print("📱 TELEGRAM NOTIFICATION SETUP")
    print("="*60)
    print()

    print("Step 1: Create Telegram Bot")
    print("-" * 60)
    print("1. Open Telegram and search for: @BotFather")
    print("2. Send: /newbot")
    print("3. Follow prompts to create bot")
    print("4. Copy the bot token")
    print()

    bot_token = input("Enter your bot token: ").strip()

    print()
    print("Step 2: Get Your Chat ID")
    print("-" * 60)
    print("1. Search for: @userinfobot")
    print("2. Send: /start")
    print("3. Copy your ID")
    print()

    chat_id = input("Enter your chat ID: ").strip()

    print()
    print("Step 3: Testing Connection...")
    print("-" * 60)

    notifier = TelegramNotifier(bot_token=bot_token, chat_id=chat_id)

    if notifier.test_connection():
        print()
        print("✅ SUCCESS! Saving configuration...")
        print()
        print("Add these to your environment:")
        print(f"export TELEGRAM_BOT_TOKEN='{bot_token}'")
        print(f"export TELEGRAM_CHAT_ID='{chat_id}'")
        print()
        print("Or add to ~/.bashrc or ~/.zshrc for persistence")
        return True
    else:
        print()
        print("❌ Connection failed. Please check your token and chat ID.")
        return False


if __name__ == "__main__":
    setup_telegram()
