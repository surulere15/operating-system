#!/usr/bin/env python3
"""
@ALPHAEDGESIGNALS - BYBIT DEPLOYMENT
$100 Capital | Bybit Futures | 10x Leverage

This script runs the live trading bot for $100 capital on Bybit.
"""

import sys
import time
from datetime import datetime
import argparse
from typing import Dict
from crypto_signals import CryptoSignalBot
from bybit_futures import BybitFuturesTrader
from telegram_notifier import TelegramNotifier


class LiveTradingBot:
    """Live trading bot integrating signals with Bybit Futures execution"""

    def __init__(self,
                 capital: float = 100.0,
                 testnet: bool = True,
                 check_interval: int = 300):
        """
        Initialize live trading bot

        Args:
            capital: Starting capital in USDT (default $100)
            testnet: Use testnet mode (default True for safety)
            check_interval: How often to check for signals in seconds (default 300 = 5 min)
        """
        self.capital = capital
        self.check_interval = check_interval

        # Initialize signal generator
        self.signal_bot = CryptoSignalBot()

        # Use standard symbols for data fetching (Binance format)
        # Expanded to 40 markets - Focus on VOLATILE alts for better returns on small capital
        self.signal_bot.symbols = [
            # Major caps (stable baseline)
            'BTC/USDT', 'ETH/USDT',

            # Large caps (good liquidity)
            'SOL/USDT', 'XRP/USDT', 'ADA/USDT', 'AVAX/USDT', 'DOT/USDT',

            # Mid caps (more volatile)
            'LINK/USDT', 'UNI/USDT', 'ATOM/USDT', 'LTC/USDT', 'BCH/USDT',
            'NEAR/USDT', 'APT/USDT', 'ARB/USDT', 'OP/USDT', 'INJ/USDT',
            'TIA/USDT', 'SEI/USDT', 'SUI/USDT',

            # High volatility alts (10-20% daily swings)
            'FET/USDT', 'RNDR/USDT', 'IMX/USDT', 'AAVE/USDT', 'CRV/USDT',
            'LDO/USDT', 'MKR/USDT', 'SNX/USDT', 'COMP/USDT',

            # Memecoins (extreme volatility - 20-50% swings)
            'DOGE/USDT', 'WIF/USDT', 'BONK/USDT', 'FLOKI/USDT',

            # Gaming/Metaverse (trending sectors)
            'SAND/USDT', 'MANA/USDT', 'AXS/USDT', 'GALA/USDT'
        ]

        # Initialize Bybit Futures trader
        self.trader = BybitFuturesTrader(
            testnet=testnet,
            capital=capital
        )

        # Initialize Telegram notifications
        self.telegram = TelegramNotifier()

        # Trading statistics
        self.stats = {
            'total_signals': 0,
            'signals_executed': 0,
            'signals_skipped': 0,
            'wins': 0,
            'losses': 0,
            'total_pnl': 0.0,
            'start_time': datetime.now()
        }

        # Leverage settings - AGGRESSIVE for $33 capital (need meaningful returns)
        self.leverage_config = {
            # Major caps (15x - increased from 10x)
            'BTC/USDT': 15, 'ETH/USDT': 15,

            # Large caps (20x - increased from 7x)
            'SOL/USDT': 20, 'XRP/USDT': 20, 'ADA/USDT': 20, 'AVAX/USDT': 20,
            'DOT/USDT': 20,

            # Mid caps (20x - increased from 5x)
            'LINK/USDT': 20, 'UNI/USDT': 20, 'ATOM/USDT': 20, 'LTC/USDT': 20,
            'BCH/USDT': 20, 'NEAR/USDT': 20, 'APT/USDT': 20, 'ARB/USDT': 20,
            'OP/USDT': 20, 'INJ/USDT': 20, 'TIA/USDT': 20, 'SEI/USDT': 20,
            'SUI/USDT': 20,

            # High volatility alts (25x - capitalize on big swings)
            'FET/USDT': 25, 'RNDR/USDT': 25, 'IMX/USDT': 25, 'AAVE/USDT': 25,
            'CRV/USDT': 25, 'LDO/USDT': 25, 'MKR/USDT': 25, 'SNX/USDT': 25,
            'COMP/USDT': 25,

            # Memecoins (15x - lower due to extreme volatility, but still aggressive)
            'DOGE/USDT': 15, 'WIF/USDT': 15, 'BONK/USDT': 15, 'FLOKI/USDT': 15,

            # Gaming/Metaverse (25x)
            'SAND/USDT': 25, 'MANA/USDT': 25, 'AXS/USDT': 25, 'GALA/USDT': 25
        }

    def execute_signal(self, signal: Dict) -> bool:
        """Execute a trading signal"""
        symbol = signal['symbol']

        # For Bybit execution, convert to perpetual format
        bybit_symbol = f"{symbol}:USDT" if ':USDT' not in symbol else symbol

        # Update signal with Bybit format for execution
        original_symbol = signal['symbol']
        signal['symbol'] = bybit_symbol

        confidence = signal['confidence']

        print(f"\n{'='*60}")
        print(f"🎯 NEW SIGNAL DETECTED")
        print(f"{'='*60}")
        print(self.signal_bot.format_signal_message(signal))

        # Send Telegram notification for signal
        self.telegram.notify_signal(signal)

        # Confidence filter
        if confidence < 60:
            print(f"⚠️  Signal confidence too low ({confidence}/100) - SKIPPING")
            self.stats['signals_skipped'] += 1
            return False

        # Get leverage for this symbol (use original symbol for lookup)
        leverage = self.leverage_config.get(original_symbol, 10)

        # Execute the trade
        order = self.trader.open_position(signal, leverage=leverage)

        if order:
            print(f"✅ Signal executed successfully!")
            self.stats['signals_executed'] += 1
            return True
        else:
            print(f"❌ Failed to execute signal")
            self.stats['signals_skipped'] += 1
            return False

    def check_and_trade(self):
        """Scan markets and execute signals"""
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Scanning markets...")

        # Scan for signals
        signals = self.signal_bot.scan_all_markets()

        if signals:
            print(f"\n🎉 Found {len(signals)} signal(s)!")

            for signal in signals:
                self.stats['total_signals'] += 1

                # Execute signal
                executed = self.execute_signal(signal)

                if executed:
                    time.sleep(2)
        else:
            print("✅ No signals at this time")

        # Monitor existing positions
        self.trader.monitor_positions()

        # Print summary
        print(self.trader.get_position_summary())

    def print_statistics(self):
        """Print trading statistics"""
        runtime = datetime.now() - self.stats['start_time']
        hours = runtime.total_seconds() / 3600

        print(f"\n{'='*60}")
        print(f"📊 TRADING STATISTICS")
        print(f"{'='*60}")
        print(f"Runtime: {hours:.1f} hours")
        print(f"Total Signals: {self.stats['total_signals']}")
        print(f"Executed: {self.stats['signals_executed']}")
        print(f"Skipped: {self.stats['signals_skipped']}")
        print(f"Win Rate: {self.stats['wins']}/{self.stats['signals_executed']} "
              f"({self.stats['wins']/self.stats['signals_executed']*100:.1f}%)" if self.stats['signals_executed'] > 0 else "N/A")
        print(f"Total P&L: ${self.stats['total_pnl']:.2f}")

        balance = self.trader.get_account_balance()
        print(f"Current Balance: ${balance['total']:.2f}")
        print(f"ROI: {(balance['total'] - self.capital) / self.capital * 100:+.2f}%")
        print(f"{'='*60}")

    def run(self, continuous: bool = True):
        """Run the trading bot"""
        print(f"\n{'='*60}")
        print(f"🚀 @ALPHAEDGESIGNALS - BYBIT LIVE TRADING BOT")
        print(f"{'='*60}")
        print(f"Capital: ${self.capital:.2f} USDT")
        print(f"Exchange: BYBIT")
        print(f"Mode: {'TESTNET (Demo)' if self.trader.testnet else '⚠️  LIVE TRADING'}")
        print(f"Markets: 40 pairs (BTC, ETH, SOL, +37 volatile alts/memes/gaming)")
        print(f"Leverage: 15-25x AGGRESSIVE (optimized for small capital)")
        print(f"Strategy: Target 10-15% moves | Keep 60%+ confidence")
        print(f"Check Interval: {self.check_interval} seconds")
        print(f"Max Daily Loss: ${self.trader.max_daily_loss:.2f}")
        print(f"Max Position Loss: ${self.trader.max_position_loss:.2f}")
        print(f"{'='*60}\n")

        # Send startup notification to Telegram
        mode = "TESTNET (Demo)" if self.trader.testnet else "LIVE TRADING"
        self.telegram.notify_startup(self.capital, "Bybit", mode)

        if not self.trader.testnet:
            print("⚠️  WARNING: LIVE TRADING MODE ENABLED!")
            print("Real money will be used. Proceed with caution.\n")
            time.sleep(3)

        try:
            if continuous:
                print("🔄 Starting continuous monitoring...")
                print("Press Ctrl+C to stop\n")

                while True:
                    self.check_and_trade()

                    runtime = (datetime.now() - self.stats['start_time']).total_seconds()
                    if runtime % 3600 < self.check_interval:
                        self.print_statistics()

                    self.trader.save_state()

                    print(f"\n⏳ Next scan in {self.check_interval} seconds...")
                    time.sleep(self.check_interval)

            else:
                self.check_and_trade()
                self.print_statistics()

        except KeyboardInterrupt:
            print("\n\n🛑 Stopping bot...")
            self.print_statistics()

            if self.trader.positions:
                print(f"\n⚠️  You have {len(self.trader.positions)} open position(s):")
                for symbol in self.trader.positions:
                    print(f"  - {symbol}")

                print("\nPositions will remain open. Use close_all_positions() to close them.")

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()

            self.trader.save_state()

    def close_all_positions(self):
        """Emergency: Close all open positions"""
        print("\n🛑 Closing all positions...")

        for symbol in list(self.trader.positions.keys()):
            result = self.trader.close_position(symbol, "Manual close - emergency")
            if result:
                pnl = result['pnl']
                if pnl > 0:
                    self.stats['wins'] += 1
                else:
                    self.stats['losses'] += 1
                self.stats['total_pnl'] += pnl

        self.print_statistics()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='@AlphaEdgeSignals Bybit Trading Bot')

    parser.add_argument('--capital', type=float, default=100.0,
                       help='Starting capital in USDT (default: 100)')

    parser.add_argument('--live', action='store_true',
                       help='Use LIVE trading (default is testnet)')

    parser.add_argument('--interval', type=int, default=300,
                       help='Check interval in seconds (default: 300 = 5 min)')

    parser.add_argument('--once', action='store_true',
                       help='Run once instead of continuously')

    args = parser.parse_args()

    # Create bot
    bot = LiveTradingBot(
        capital=args.capital,
        testnet=not args.live,
        check_interval=args.interval
    )

    # Run
    bot.run(continuous=not args.once)


if __name__ == "__main__":
    main()
