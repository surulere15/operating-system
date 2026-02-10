#!/usr/bin/env python3
"""
Telegram Bot for Crypto Signals
Automatically posts signals to your Telegram channel
"""

import os
import requests
from crypto_signals import CryptoSignalBot
from datetime import datetime

# Configuration (set these as environment variables or hardcode for testing)
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
TELEGRAM_CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID', 'YOUR_CHANNEL_ID_HERE')

class TelegramNotifier:
    """Send signal notifications to Telegram"""

    def __init__(self, bot_token, channel_id):
        self.bot_token = bot_token
        self.channel_id = channel_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"

    def send_message(self, text, parse_mode='Markdown'):
        """Send message to Telegram channel"""
        url = f"{self.base_url}/sendMessage"
        payload = {
            'chat_id': self.channel_id,
            'text': text,
            'parse_mode': parse_mode,
            'disable_web_page_preview': True
        }

        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"❌ Error sending to Telegram: {e}")
            return False

    def format_signal(self, signal):
        """Format signal for Telegram (Markdown)"""
        emoji = "🟢" if signal['type'] == 'BUY' else "🔴"

        # Create clickable TradingView link
        symbol_clean = signal['symbol'].replace('/', '').replace('USDT', '')
        tv_link = f"https://www.tradingview.com/chart/?symbol=KRAKEN:{signal['symbol'].replace('/', '')}"

        message = f"""
{emoji} *{signal['type']} SIGNAL* - {signal['symbol']}

💰 *Entry Price:* ${signal['price']:.4f}

🎯 *Targets:*
   TP1: ${signal['take_profit_1']:.4f} (+5%)
   TP2: ${signal['take_profit_2']:.4f} (+10%)
   TP3: ${signal['take_profit_3']:.4f} (+15%)

🛑 *Stop Loss:* ${signal['stop_loss']:.4f} (-5%)

📊 *Technical Analysis:*
   • RSI: {signal['indicators']['rsi']}
   • MACD: {signal['indicators']['macd']:.2f}
   • Signal Line: {signal['indicators']['signal_line']:.2f}
   • Volume: {signal['indicators']['volume_surge']:.1f}x average
   • 24h Change: {signal['indicators']['price_change_24h']:.2f}%

💡 *Reason:* {signal['reason']}

⭐ *Confidence:* {signal['confidence']}/100

📈 [View Chart on TradingView]({tv_link})

⏰ _{datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}_
        """.strip()

        return message

    def send_signal(self, signal):
        """Send formatted signal to channel"""
        message = self.format_signal(signal)
        success = self.send_message(message)

        if success:
            print(f"✅ Sent {signal['type']} signal for {signal['symbol']} to Telegram")
        else:
            print(f"❌ Failed to send signal for {signal['symbol']}")

        return success

    def send_scan_summary(self, total_scanned, signals_found):
        """Send scan summary to channel"""
        message = f"""
📊 *Market Scan Complete*

Analyzed: {total_scanned} markets
Signals Found: {signals_found}

{self._get_status_emoji(signals_found)} {'Strong opportunities detected!' if signals_found > 0 else 'No high-probability setups at this time.'}

⏰ _{datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}_
        """.strip()

        return self.send_message(message)

    def _get_status_emoji(self, count):
        """Get emoji based on signal count"""
        if count == 0:
            return "✅"
        elif count <= 2:
            return "🎯"
        else:
            return "🚀"


def main():
    """Main execution - scan and post to Telegram"""

    print("="*60)
    print("🤖 CRYPTO SIGNAL BOT + TELEGRAM")
    print("="*60)

    # Validate configuration
    if TELEGRAM_BOT_TOKEN == 'YOUR_BOT_TOKEN_HERE':
        print("\n❌ ERROR: Please set TELEGRAM_BOT_TOKEN")
        print("Get it from @BotFather on Telegram")
        print("\nSet it as environment variable:")
        print("export TELEGRAM_BOT_TOKEN='123456789:ABCdef...'")
        return

    if TELEGRAM_CHANNEL_ID == 'YOUR_CHANNEL_ID_HERE':
        print("\n❌ ERROR: Please set TELEGRAM_CHANNEL_ID")
        print("Example: -1001234567890")
        print("\nSet it as environment variable:")
        print("export TELEGRAM_CHANNEL_ID='-1001234567890'")
        return

    # Initialize
    bot = CryptoSignalBot()
    notifier = TelegramNotifier(TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID)

    # Scan markets
    signals = bot.scan_all_markets()

    # Send signals to Telegram
    if signals:
        print(f"\n🎉 Found {len(signals)} signals! Sending to Telegram...\n")

        for signal in signals:
            # Print to console
            print(bot.format_signal_message(signal))
            print("-"*60)

            # Send to Telegram
            notifier.send_signal(signal)

        # Send summary
        notifier.send_scan_summary(len(bot.symbols), len(signals))

        print(f"\n✅ All signals sent to Telegram!")
    else:
        print("\n✅ No signals at this time. Markets are stable.")
        # Optionally send "no signals" update (comment out if you don't want this)
        # notifier.send_scan_summary(len(bot.symbols), 0)

    # Save to file as backup
    bot.save_signals(signals)


if __name__ == "__main__":
    main()
