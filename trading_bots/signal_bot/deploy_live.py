#!/usr/bin/env python3
"""
@ALPHAEDGESIGNALS - LIVE DEPLOYMENT
$100 Capital | Binance Futures | 10x Leverage

This script runs the live trading bot for $100 capital deployment.
"""

import sys
import time
from datetime import datetime
import argparse
from typing import Dict
from crypto_signals import CryptoSignalBot
from binance_futures import BinanceFuturesTrader


class LiveTradingBot:
    """Live trading bot integrating signals with Binance Futures execution"""

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

        # Filter to only BTC, ETH, SOL for $100 capital
        self.signal_bot.symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']

        # Initialize Binance Futures trader
        self.trader = BinanceFuturesTrader(
            testnet=testnet,
            capital=capital
        )

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

        # Leverage settings per asset
        self.leverage_config = {
            'BTC/USDT': 10,  # 10x for BTC (lowest volatility)
            'ETH/USDT': 10,  # 10x for ETH
            'SOL/USDT': 5    # 5x for SOL (higher volatility)
        }

    def execute_signal(self, signal: Dict) -> bool:
        """
        Execute a trading signal

        Args:
            signal: Signal from CryptoSignalBot

        Returns:
            True if executed, False if skipped
        """
        symbol = signal['symbol']
        confidence = signal['confidence']

        print(f"\n{'='*60}")
        print(f"🎯 NEW SIGNAL DETECTED")
        print(f"{'='*60}")
        print(self.signal_bot.format_signal_message(signal))

        # Confidence filter: Only execute high-confidence signals
        if confidence < 60:
            print(f"⚠️  Signal confidence too low ({confidence}/100) - SKIPPING")
            self.stats['signals_skipped'] += 1
            return False

        # Get leverage for this symbol
        leverage = self.leverage_config.get(symbol, 10)

        # Ask for confirmation (optional - can be disabled for full automation)
        if not self.trader.testnet:
            print(f"\n⚠️  LIVE MODE - Confirm execution?")
            print(f"Symbol: {symbol} | Type: {signal['type']} | Confidence: {confidence}/100")
            print(f"Leverage: {leverage}x | Capital Risk: ~${self.trader.max_position_loss:.2f}")

            # For live trading, you might want to add confirmation
            # For now, we'll auto-execute in both modes

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

                # Wait a bit between executions
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
        """
        Run the trading bot

        Args:
            continuous: If True, run continuously. If False, run once.
        """
        print(f"\n{'='*60}")
        print(f"🚀 @ALPHAEDGESIGNALS - LIVE TRADING BOT")
        print(f"{'='*60}")
        print(f"Capital: ${self.capital:.2f} USDT")
        print(f"Mode: {'TESTNET (Demo)' if self.trader.testnet else '⚠️  LIVE TRADING'}")
        print(f"Assets: {', '.join(self.signal_bot.symbols)}")
        print(f"Leverage: BTC/ETH 10x, SOL 5x")
        print(f"Check Interval: {self.check_interval} seconds")
        print(f"Max Daily Loss: ${self.trader.max_daily_loss:.2f}")
        print(f"Max Position Loss: ${self.trader.max_position_loss:.2f}")
        print(f"{'='*60}\n")

        if not self.trader.testnet:
            print("⚠️  WARNING: LIVE TRADING MODE ENABLED!")
            print("Real money will be used. Proceed with caution.\n")
            time.sleep(3)

        try:
            if continuous:
                print("🔄 Starting continuous monitoring...")
                print("Press Ctrl+C to stop\n")

                while True:
                    # Check and trade
                    self.check_and_trade()

                    # Print stats every hour
                    runtime = (datetime.now() - self.stats['start_time']).total_seconds()
                    if runtime % 3600 < self.check_interval:  # Every hour
                        self.print_statistics()

                    # Save state
                    self.trader.save_state()

                    # Wait for next check
                    print(f"\n⏳ Next scan in {self.check_interval} seconds...")
                    time.sleep(self.check_interval)

            else:
                # Single run
                self.check_and_trade()
                self.print_statistics()

        except KeyboardInterrupt:
            print("\n\n🛑 Stopping bot...")
            self.print_statistics()

            # Ask to close positions
            if self.trader.positions:
                print(f"\n⚠️  You have {len(self.trader.positions)} open position(s):")
                for symbol in self.trader.positions:
                    print(f"  - {symbol}")

                print("\nPositions will remain open. Use close_all_positions() to close them.")

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()

            # Save state on error
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
    parser = argparse.ArgumentParser(description='@AlphaEdgeSignals Live Trading Bot')

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
