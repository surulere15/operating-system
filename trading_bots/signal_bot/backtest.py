#!/usr/bin/env python3
"""
BACKTEST MODULE - Test crypto signal bot on historical data
Measures actual performance over 1-2 years of real market data
"""

import ccxt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
from crypto_signals import CryptoSignalBot

class Backtester:
    """Backtest trading signals on historical data"""

    def __init__(self, initial_capital=10000):
        self.bot = CryptoSignalBot()
        self.initial_capital = initial_capital
        self.results = []
        self.trades = []

    def fetch_historical_data(self, symbol, days=365):
        """Fetch historical OHLCV data"""
        print(f"  Downloading {days} days of data for {symbol}...")

        try:
            # Calculate timestamp for days ago
            since = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)

            # Fetch all historical data
            all_ohlcv = []
            current_since = since

            while True:
                ohlcv = ccxt.kraken().fetch_ohlcv(
                    symbol,
                    timeframe='1h',
                    since=current_since,
                    limit=1000
                )

                if not ohlcv:
                    break

                all_ohlcv.extend(ohlcv)

                # Move to next batch
                current_since = ohlcv[-1][0] + 1

                # If we've reached current time, stop
                if current_since >= int(datetime.now().timestamp() * 1000):
                    break

                time.sleep(1)  # Rate limiting

            df = pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

            print(f"    ✓ Downloaded {len(df)} candles ({df['timestamp'].min()} to {df['timestamp'].max()})")
            return df

        except Exception as e:
            print(f"    ✗ Error: {e}")
            return None

    def simulate_trade(self, signal, price_data_after_signal):
        """Simulate a trade based on signal and subsequent price action"""
        entry_price = signal['price']
        stop_loss = signal['stop_loss']
        take_profit_1 = signal['take_profit_1']
        take_profit_2 = signal['take_profit_2']
        take_profit_3 = signal['take_profit_3']

        # Track what happened after signal
        for i, row in price_data_after_signal.iterrows():
            high = row['high']
            low = row['low']

            if signal['type'] == 'BUY':
                # Check if stop loss hit
                if low <= stop_loss:
                    pnl_pct = ((stop_loss - entry_price) / entry_price) * 100
                    return {
                        'exit_price': stop_loss,
                        'exit_reason': 'Stop Loss',
                        'pnl_pct': pnl_pct,
                        'bars_held': i + 1
                    }

                # Check take profit levels (use highest hit)
                if high >= take_profit_3:
                    pnl_pct = ((take_profit_3 - entry_price) / entry_price) * 100
                    return {
                        'exit_price': take_profit_3,
                        'exit_reason': 'TP3 (+15%)',
                        'pnl_pct': pnl_pct,
                        'bars_held': i + 1
                    }
                elif high >= take_profit_2:
                    pnl_pct = ((take_profit_2 - entry_price) / entry_price) * 100
                    return {
                        'exit_price': take_profit_2,
                        'exit_reason': 'TP2 (+10%)',
                        'pnl_pct': pnl_pct,
                        'bars_held': i + 1
                    }
                elif high >= take_profit_1:
                    pnl_pct = ((take_profit_1 - entry_price) / entry_price) * 100
                    return {
                        'exit_price': take_profit_1,
                        'exit_reason': 'TP1 (+5%)',
                        'pnl_pct': pnl_pct,
                        'bars_held': i + 1
                    }

            else:  # SELL
                # Check if stop loss hit
                if high >= stop_loss:
                    pnl_pct = ((entry_price - stop_loss) / entry_price) * 100
                    return {
                        'exit_price': stop_loss,
                        'exit_reason': 'Stop Loss',
                        'pnl_pct': pnl_pct,
                        'bars_held': i + 1
                    }

                # Check take profit levels
                if low <= take_profit_3:
                    pnl_pct = ((entry_price - take_profit_3) / entry_price) * 100
                    return {
                        'exit_price': take_profit_3,
                        'exit_reason': 'TP3 (+15%)',
                        'pnl_pct': pnl_pct,
                        'bars_held': i + 1
                    }
                elif low <= take_profit_2:
                    pnl_pct = ((entry_price - take_profit_2) / entry_price) * 100
                    return {
                        'exit_price': take_profit_2,
                        'exit_reason': 'TP2 (+10%)',
                        'pnl_pct': pnl_pct,
                        'bars_held': i + 1
                    }
                elif low <= take_profit_1:
                    pnl_pct = ((entry_price - take_profit_1) / entry_price) * 100
                    return {
                        'exit_price': take_profit_1,
                        'exit_reason': 'TP1 (+5%)',
                        'pnl_pct': pnl_pct,
                        'bars_held': i + 1
                    }

        # If no exit after 100 bars, force exit at market
        last_price = price_data_after_signal.iloc[-1]['close']
        if signal['type'] == 'BUY':
            pnl_pct = ((last_price - entry_price) / entry_price) * 100
        else:
            pnl_pct = ((entry_price - last_price) / entry_price) * 100

        return {
            'exit_price': last_price,
            'exit_reason': 'Timeout (100 bars)',
            'pnl_pct': pnl_pct,
            'bars_held': len(price_data_after_signal)
        }

    def backtest_symbol(self, symbol, days=365):
        """Run backtest on one symbol"""
        print(f"\n📊 Backtesting {symbol}")
        print("="*60)

        # Fetch historical data
        df = self.fetch_historical_data(symbol, days)
        if df is None or len(df) < 250:
            print("  ✗ Insufficient data (need at least 250 candles for 200-period MA)")
            return None

        # Scan through historical data
        signals_found = 0

        # Need at least 250 candles for 200-period MA + 100 for trade simulation
        for i in range(250, len(df) - 100):
            # Temporarily replace bot's fetch method to return historical slice
            historical_slice = df.iloc[:i+1].copy()

            # Save original fetch method
            original_fetch = self.bot.fetch_ohlcv

            # Override to return historical slice
            self.bot.fetch_ohlcv = lambda sym: historical_slice if sym == symbol else None

            # Use bot's analyze_market method (includes trend filter!)
            signal = self.bot.analyze_market(symbol)

            # Restore original fetch method
            self.bot.fetch_ohlcv = original_fetch

            if signal:
                # Add timestamp
                signal['timestamp'] = historical_slice['timestamp'].iloc[-1]

                # Simulate trade with subsequent data
                future_data = df.iloc[i+1:i+101]
                trade_result = self.simulate_trade(signal, future_data)

                # Record trade
                self.trades.append({
                    **signal,
                    **trade_result
                })

                signals_found += 1
                print(f"  Signal #{signals_found}: {signal['type']} at ${signal['price']:.2f} ({signal['indicators']['trend']}) → {trade_result['exit_reason']} → {trade_result['pnl_pct']:+.2f}%")

        print(f"\n  ✓ Found {signals_found} signals in {days} days")
        return signals_found

    def calculate_metrics(self):
        """Calculate performance metrics"""
        if not self.trades:
            return None

        df = pd.DataFrame(self.trades)

        # Basic metrics
        total_trades = len(df)
        winners = df[df['pnl_pct'] > 0]
        losers = df[df['pnl_pct'] < 0]

        win_rate = (len(winners) / total_trades) * 100

        avg_win = winners['pnl_pct'].mean() if len(winners) > 0 else 0
        avg_loss = losers['pnl_pct'].mean() if len(losers) > 0 else 0

        total_pnl = df['pnl_pct'].sum()
        avg_pnl = df['pnl_pct'].mean()

        # Risk metrics
        sharpe = (avg_pnl / df['pnl_pct'].std()) if df['pnl_pct'].std() > 0 else 0

        # Max drawdown (cumulative P&L)
        cumulative_pnl = df['pnl_pct'].cumsum()
        running_max = cumulative_pnl.cummax()
        drawdown = running_max - cumulative_pnl
        max_drawdown = drawdown.max()

        # Best/worst trades
        best_trade = df.loc[df['pnl_pct'].idxmax()] if len(df) > 0 else None
        worst_trade = df.loc[df['pnl_pct'].idxmin()] if len(df) > 0 else None

        # By signal type
        buy_signals = df[df['type'] == 'BUY']
        sell_signals = df[df['type'] == 'SELL']

        return {
            'total_trades': total_trades,
            'winners': len(winners),
            'losers': len(losers),
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'total_pnl': total_pnl,
            'avg_pnl': avg_pnl,
            'sharpe_ratio': sharpe,
            'max_drawdown': max_drawdown,
            'best_trade': best_trade,
            'worst_trade': worst_trade,
            'buy_signals': len(buy_signals),
            'sell_signals': len(sell_signals),
            'buy_win_rate': (len(buy_signals[buy_signals['pnl_pct'] > 0]) / len(buy_signals) * 100) if len(buy_signals) > 0 else 0,
            'sell_win_rate': (len(sell_signals[sell_signals['pnl_pct'] > 0]) / len(sell_signals) * 100) if len(sell_signals) > 0 else 0,
            'avg_bars_held': df['bars_held'].mean(),
        }

    def print_report(self, metrics):
        """Print detailed performance report"""
        print("\n" + "="*60)
        print("📊 BACKTEST RESULTS - PERFORMANCE REPORT")
        print("="*60)

        print(f"\n🎯 OVERALL PERFORMANCE:")
        print(f"  Total Trades: {metrics['total_trades']}")
        print(f"  Winners: {metrics['winners']} ✅")
        print(f"  Losers: {metrics['losers']} ❌")
        print(f"  Win Rate: {metrics['win_rate']:.1f}%")

        print(f"\n💰 PROFITABILITY:")
        print(f"  Average Win: +{metrics['avg_win']:.2f}%")
        print(f"  Average Loss: {metrics['avg_loss']:.2f}%")
        print(f"  Average P&L per Trade: {metrics['avg_pnl']:+.2f}%")
        print(f"  Total P&L: {metrics['total_pnl']:+.2f}%")

        # Calculate expected value
        win_rate_decimal = metrics['win_rate'] / 100
        expected_value = (win_rate_decimal * metrics['avg_win']) + ((1 - win_rate_decimal) * metrics['avg_loss'])
        print(f"  Expected Value per Trade: {expected_value:+.2f}%")

        print(f"\n⚠️ RISK METRICS:")
        print(f"  Max Drawdown: {metrics['max_drawdown']:.2f}%")
        print(f"  Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
        print(f"  Average Hold Time: {metrics['avg_bars_held']:.0f} hours")

        print(f"\n📈 BY SIGNAL TYPE:")
        print(f"  BUY Signals: {metrics['buy_signals']} ({metrics['buy_win_rate']:.1f}% win rate)")
        print(f"  SELL Signals: {metrics['sell_signals']} ({metrics['sell_win_rate']:.1f}% win rate)")

        print(f"\n🏆 BEST TRADE:")
        if metrics['best_trade'] is not None:
            bt = metrics['best_trade']
            print(f"  {bt['type']} {bt['symbol']} at ${bt['price']:.2f}")
            print(f"  Exit: {bt['exit_reason']} → {bt['pnl_pct']:+.2f}%")
            print(f"  Date: {bt['timestamp']}")

        print(f"\n💔 WORST TRADE:")
        if metrics['worst_trade'] is not None:
            wt = metrics['worst_trade']
            print(f"  {wt['type']} {wt['symbol']} at ${wt['price']:.2f}")
            print(f"  Exit: {wt['exit_reason']} → {wt['pnl_pct']:+.2f}%")
            print(f"  Date: {wt['timestamp']}")

        # Verdict
        print("\n" + "="*60)
        print("🎯 VERDICT:")

        if metrics['win_rate'] >= 60 and expected_value > 1.0:
            print("  ✅ EXCELLENT - Strong profitable system")
            print("  💰 Ready to launch with confidence")
        elif metrics['win_rate'] >= 55 and expected_value > 0.5:
            print("  ✅ GOOD - Profitable system")
            print("  💰 Launch with realistic expectations")
        elif metrics['win_rate'] >= 50 and expected_value > 0:
            print("  ⚠️  MARGINAL - Barely profitable")
            print("  🔧 Consider optimization before launch")
        else:
            print("  ❌ UNPROFITABLE - Needs improvement")
            print("  🔧 Optimize parameters or add filters")

        print("="*60)


def main():
    """Run backtest on all symbols"""
    print("="*60)
    print("🔬 CRYPTO SIGNAL BOT - BACKTESTING")
    print("="*60)
    print("\nTesting bot performance on 1 year of historical data...")
    print("This may take 10-15 minutes to download and analyze.\n")

    backtester = Backtester(initial_capital=10000)

    # Test on main symbols (skip MATIC since Kraken doesn't have it)
    test_symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'XRP/USDT', 'ADA/USDT']

    print(f"Testing on {len(test_symbols)} symbols: {', '.join(test_symbols)}")

    for symbol in test_symbols:
        try:
            backtester.backtest_symbol(symbol, days=365)
        except Exception as e:
            print(f"  ✗ Error backtesting {symbol}: {e}")
            continue

    # Calculate and display results
    if backtester.trades:
        metrics = backtester.calculate_metrics()
        backtester.print_report(metrics)

        # Save detailed results
        trades_df = pd.DataFrame(backtester.trades)
        output_file = "/tmp/backtest_results.csv"
        trades_df.to_csv(output_file, index=False)
        print(f"\n💾 Detailed results saved to: {output_file}")
    else:
        print("\n❌ No trades found in backtest period")
        print("This could mean:")
        print("  - Market conditions didn't trigger signals")
        print("  - Signal criteria too strict")
        print("  - Consider adjusting RSI/MACD thresholds")


if __name__ == "__main__":
    main()
