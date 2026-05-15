#!/usr/bin/env python3
import time
import os
import sys
import argparse
from datetime import datetime
from crypto_signals import CryptoSignalBot
from telegram_bot import TelegramNotifier

# Environment variables found in .bashrc
BOT_TOKEN = '8287512169:AAFxp43KbygeiButp_3HkRvcRQ4-kt4pqnA'
# Mapping TELEGRAM_CHAT_ID from .bashrc to what telegram_bot.py expects
CHANNEL_ID = '6861293466' 

def run_scout(notifier, bot, test_run=False):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting Market Scan...")
    
    try:
        # Scan markets
        signals = bot.scan_all_markets()
        
        if signals:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Found {len(signals)} signals. Sending to Telegram...")
            for signal in signals:
                notifier.send_signal(signal)
            notifier.send_scan_summary(len(bot.symbols), len(signals))
        else:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] No high-probability signals found.")
            # Un-comment the line below if you want "no signal" summaries in Telegram
            # notifier.send_scan_summary(len(bot.symbols), 0)
            
        bot.save_signals(signals)
        
    except Exception as e:
        print(f"❌ Error during scan: {e}")

    if test_run:
        print("\n✅ Test run complete. Exiting...")
        sys.exit(0)

def main():
    parser = argparse.ArgumentParser(description="Continuous Crypto Signal Scout")
    parser.add_argument("--test-run", action="store_true", help="Run once and exit")
    parser.add_argument("--interval", type=int, default=300, help="Interval between scans in seconds (default: 300)")
    args = parser.parse_args()

    print("="*60)
    print("🤖 CONTINUOUS SIGNAL SCOUT - ACTIVE")
    print(f"Settings: Interval={args.interval}s | Bot={BOT_TOKEN[:10]}... | Chat={CHANNEL_ID}")
    print("="*60)

    # Initialize components
    bot = CryptoSignalBot()
    # Ensure environment variables are set for internal script logic if they use os.getenv
    os.environ['TELEGRAM_BOT_TOKEN'] = BOT_TOKEN
    os.environ['TELEGRAM_CHANNEL_ID'] = CHANNEL_ID
    
    notifier = TelegramNotifier(BOT_TOKEN, CHANNEL_ID)

    if args.test_run:
        run_scout(notifier, bot, test_run=True)
    
    while True:
        run_scout(notifier, bot)
        print(f"⏳ Sleeping for {args.interval} seconds...")
        time.sleep(args.interval)

if __name__ == "__main__":
    main()
