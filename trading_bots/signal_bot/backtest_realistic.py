#!/usr/bin/env python3
"""
REALISTIC BACKTEST - Tests bot under worst-case conditions
Includes: slippage, trading fees, partial fills, volatility spikes
"""

import ccxt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import random
from crypto_signals import CryptoSignalBot

class RealisticBacktester:
    """Backtest with real-world uncertainties"""

    def __init__(self, initial_capital=10000):
        self.bot = CryptoSignalBot()
        self.initial_capital = initial_capital
        self.results = []
        self.trades = []

        # Trading costs and uncertainties
        self.maker_fee = 0.001  # 0.1% maker fee
        self.taker_fee = 0.001  # 0.1% taker fee
        self.slippage_range = (0.0005, 0.002)  # 0.05% to 0.2% slippage
        self.partial_fill_chance = 0.1  # 10% chance of not filling

    def fetch_historical_data(self, symbol, days=365):
        """Fetch historical OHLCV data"""
        print(f"  Downloading {days} days of data for {symbol}...")

        try:
            since = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)
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
                current_since = ohlcv[-1][0] + 1

                if current_since >= int(datetime.now().timestamp() * 1000):
                    break

                time.sleep(1)

            df = pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

            print(f"    ✓ Downloaded {len(df)} candles ({df['timestamp'].min()} to {df['timestamp'].max()})")
            return df

        except Exception as e:
            print(f"    ✗ Error: {e}")
            return None

    def apply_entry_slippage(self, signal_price, signal_type):
        """
        Apply realistic entry slippage
        Market orders get worse prices during volatility
        """
        # Random slippage between 0.05% and 0.2%
        slippage_pct = random.uniform(*self.slippage_range)

        if signal_type == 'BUY':
            # Buy orders slip UP (pay more)
            actual_entry = signal_price * (1 + slippage_pct)
        else:
            # Sell orders slip DOWN (receive less)
            actual_entry = signal_price * (1 - slippage_pct)

        return actual_entry

    def check_partial_fill(self):
        """
        Sometimes orders don't fill (low liquidity, fast moves)
        """
        return random.random() > self.partial_fill_chance

    def simulate_realistic_trade(self, signal, price_data_after_signal):
        """
        Simulate trade with realistic conditions:
        - Entry slippage
        - Partial fills
        - Trading fees
        - Worst-case scenarios
        """
        # Check if order fills
        if not self.check_partial_fill():
            return {
                'exit_price': signal['price'],
                'exit_reason': 'Partial Fill (No Entry)',
                'pnl_pct': -self.taker_fee * 100,  # Lost fees
                'bars_held': 0
            }

        # Apply entry slippage
        actual_entry = self.apply_entry_slippage(signal['price'], signal['type'])

        # Apply entry fee
        entry_cost = actual_entry * (1 + self.taker_fee)

        # Recalculate stops and targets based on actual entry
        if signal['type'] == 'BUY':
            stop_loss = actual_entry * 0.97  # 3% stop for range, 5% for trend
            take_profit_1 = actual_entry * 1.03
            take_profit_2 = actual_entry * 1.05
            take_profit_3 = actual_entry * 1.07
        else:
            stop_loss = actual_entry * 1.03
            take_profit_1 = actual_entry * 0.97
            take_profit_2 = actual_entry * 0.95
            take_profit_3 = actual_entry * 0.93

        # Simulate price action
        for i, row in price_data_after_signal.iterrows():
            high = row['high']
            low = row['low']
            close = row['close']

            # Add random volatility spikes (5% chance)
            if random.random() < 0.05:
                spike_pct = random.uniform(0.01, 0.03)  # 1-3% spike
                if random.random() < 0.5:
                    high *= (1 + spike_pct)
                else:
                    low *= (1 - spike_pct)

            if signal['type'] == 'BUY':
                # Check stop loss first (worst case - assume stop fills at worse price)
                if low <= stop_loss:
                    # Slippage on stop loss (usually worse)
                    stop_slippage = random.uniform(0.001, 0.005)  # 0.1-0.5% worse
                    actual_exit = stop_loss * (1 - stop_slippage)
                    exit_after_fees = actual_exit * (1 - self.taker_fee)
                    pnl_pct = ((exit_after_fees - entry_cost) / entry_cost) * 100

                    return {
                        'exit_price': actual_exit,
                        'exit_reason': 'Stop Loss (with slippage)',
                        'pnl_pct': pnl_pct,
                        'bars_held': i + 1
                    }

                # Check take profits (assume limit orders fill at price)
                if high >= take_profit_3:
                    exit_after_fees = take_profit_3 * (1 - self.maker_fee)
                    pnl_pct = ((exit_after_fees - entry_cost) / entry_cost) * 100
                    return {
                        'exit_price': take_profit_3,
                        'exit_reason': 'TP3',
                        'pnl_pct': pnl_pct,
                        'bars_held': i + 1
                    }
                elif high >= take_profit_2:
                    exit_after_fees = take_profit_2 * (1 - self.maker_fee)
                    pnl_pct = ((exit_after_fees - entry_cost) / entry_cost) * 100
                    return {
                        'exit_price': take_profit_2,
                        'exit_reason': 'TP2',
                        'pnl_pct': pnl_pct,
                        'bars_held': i + 1
                    }
                elif high >= take_profit_1:
                    exit_after_fees = take_profit_1 * (1 - self.maker_fee)
                    pnl_pct = ((exit_after_fees - entry_cost) / entry_cost) * 100
                    return {
                        'exit_price': take_profit_1,
                        'exit_reason': 'TP1',
                        'pnl_pct': pnl_pct,
                        'bars_held': i + 1
                    }

            else:  # SELL
                # Check stop loss
                if high >= stop_loss:
                    stop_slippage = random.uniform(0.001, 0.005)
                    actual_exit = stop_loss * (1 + stop_slippage)
                    exit_after_fees = actual_exit * (1 + self.taker_fee)
                    pnl_pct = ((entry_cost - exit_after_fees) / entry_cost) * 100

                    return {
                        'exit_price': actual_exit,
                        'exit_reason': 'Stop Loss (with slippage)',
                        'pnl_pct': pnl_pct,
                        'bars_held': i + 1
                    }

                # Check take profits
                if low <= take_profit_3:
                    exit_after_fees = take_profit_3 * (1 + self.maker_fee)
                    pnl_pct = ((entry_cost - exit_after_fees) / entry_cost) * 100
                    return {
                        'exit_price': take_profit_3,
                        'exit_reason': 'TP3',
                        'pnl_pct': pnl_pct,
                        'bars_held': i + 1
                    }
                elif low <= take_profit_2:
                    exit_after_fees = take_profit_2 * (1 + self.maker_fee)
                    pnl_pct = ((entry_cost - exit_after_fees) / entry_cost) * 100
                    return {
                        'exit_price': take_profit_2,
                        'exit_reason': 'TP2',
                        'pnl_pct': pnl_pct,
                        'bars_held': i + 1
                    }
                elif low <= take_profit_1:
                    exit_after_fees = take_profit_1 * (1 + self.maker_fee)
                    pnl_pct = ((entry_cost - exit_after_fees) / entry_cost) * 100
                    return {
                        'exit_price': take_profit_1,
                        'exit_reason': 'TP1',
                        'pnl_pct': pnl_pct,
                        'bars_held': i + 1
                    }

        # Timeout - force exit at market (with slippage)
        last_price = price_data_after_signal.iloc[-1]['close']
        market_slippage = random.uniform(0.001, 0.003)

        if signal['type'] == 'BUY':
            actual_exit = last_price * (1 - market_slippage)
            exit_after_fees = actual_exit * (1 - self.taker_fee)
            pnl_pct = ((exit_after_fees - entry_cost) / entry_cost) * 100
        else:
            actual_exit = last_price * (1 + market_slippage)
            exit_after_fees = actual_exit * (1 + self.taker_fee)
            pnl_pct = ((entry_cost - exit_after_fees) / entry_cost) * 100

        return {
            'exit_price': actual_exit,
            'exit_reason': 'Timeout (100 bars)',
            'pnl_pct': pnl_pct,
            'bars_held': len(price_data_after_signal)
        }

    def backtest_symbol(self, symbol, days=365):
        """Run realistic backtest on one symbol"""
        print(f"\n📊 Backtesting {symbol} (REALISTIC MODE)")
        print("="*60)

        df = self.fetch_historical_data(symbol, days)
        if df is None or len(df) < 250:
            print("  ✗ Insufficient data")
            return None

        signals_found = 0

        for i in range(250, len(df) - 100):
            historical_slice = df.iloc[:i+1].copy()

            # Save original fetch method
            original_fetch = self.bot.fetch_ohlcv
            self.bot.fetch_ohlcv = lambda sym: historical_slice if sym == symbol else None

            signal = self.bot.analyze_market(symbol)

            # Restore original fetch
            self.bot.fetch_ohlcv = original_fetch

            if signal:
                signal['timestamp'] = historical_slice['timestamp'].iloc[-1]

                # Simulate with realistic conditions
                future_data = df.iloc[i+1:i+101]
                trade_result = self.simulate_realistic_trade(signal, future_data)

                self.trades.append({
                    **signal,
                    **trade_result
                })

                signals_found += 1
                print(f"  Signal #{signals_found}: {signal['type']} at ${signal['price']:.2f} ({signal['indicators']['trend']}) → {trade_result['exit_reason']} → {trade_result['pnl_pct']:+.2f}%")

        print(f"\n  ✓ Found {signals_found} signals")
        return signals_found

    def calculate_metrics(self):
        """Calculate performance metrics"""
        if not self.trades:
            return None

        df = pd.DataFrame(self.trades)

        total_trades = len(df)
        winners = df[df['pnl_pct'] > 0]
        losers = df[df['pnl_pct'] <= 0]

        win_rate = (len(winners) / total_trades) * 100
        avg_win = winners['pnl_pct'].mean() if len(winners) > 0 else 0
        avg_loss = losers['pnl_pct'].mean() if len(losers) > 0 else 0
        total_pnl = df['pnl_pct'].sum()
        avg_pnl = df['pnl_pct'].mean()

        sharpe = (avg_pnl / df['pnl_pct'].std()) if df['pnl_pct'].std() > 0 else 0

        cumulative_pnl = df['pnl_pct'].cumsum()
        running_max = cumulative_pnl.cummax()
        drawdown = running_max - cumulative_pnl
        max_drawdown = drawdown.max()

        best_trade = df.loc[df['pnl_pct'].idxmax()] if len(df) > 0 else None
        worst_trade = df.loc[df['pnl_pct'].idxmin()] if len(df) > 0 else None

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
            'avg_bars_held': df['bars_held'].mean(),
        }

    def print_report(self, metrics):
        """Print detailed performance report"""
        print("\n" + "="*60)
        print("📊 REALISTIC BACKTEST RESULTS")
        print("="*60)
        print("\n🎲 INCLUDES REAL-WORLD UNCERTAINTIES:")
        print("  • Entry slippage (0.05-0.2%)")
        print("  • Trading fees (0.1% maker/taker)")
        print("  • Stop loss slippage (0.1-0.5% worse)")
        print("  • Partial fills (10% chance)")
        print("  • Volatility spikes (5% random)")

        print(f"\n🎯 OVERALL PERFORMANCE:")
        print(f"  Total Trades: {metrics['total_trades']}")
        print(f"  Winners: {metrics['winners']} ✅")
        print(f"  Losers: {metrics['losers']} ❌")
        print(f"  Win Rate: {metrics['win_rate']:.1f}%")

        print(f"\n💰 PROFITABILITY (AFTER FEES & SLIPPAGE):")
        print(f"  Average Win: +{metrics['avg_win']:.2f}%")
        print(f"  Average Loss: {metrics['avg_loss']:.2f}%")
        print(f"  Average P&L per Trade: {metrics['avg_pnl']:+.2f}%")
        print(f"  Total P&L: {metrics['total_pnl']:+.2f}%")

        win_rate_decimal = metrics['win_rate'] / 100
        expected_value = (win_rate_decimal * metrics['avg_win']) + ((1 - win_rate_decimal) * metrics['avg_loss'])
        print(f"  Expected Value per Trade: {expected_value:+.2f}%")

        print(f"\n⚠️ RISK METRICS:")
        print(f"  Max Drawdown: {metrics['max_drawdown']:.2f}%")
        print(f"  Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")

        print(f"\n🏆 BEST TRADE:")
        if metrics['best_trade'] is not None:
            bt = metrics['best_trade']
            print(f"  {bt['type']} {bt['symbol']} → {bt['pnl_pct']:+.2f}%")

        print(f"\n💔 WORST TRADE:")
        if metrics['worst_trade'] is not None:
            wt = metrics['worst_trade']
            print(f"  {wt['type']} {wt['symbol']} → {wt['pnl_pct']:+.2f}%")

        print("\n" + "="*60)
        print("🎯 REALISTIC VERDICT:")

        if metrics['win_rate'] >= 55 and expected_value > 0.5:
            print("  ✅ PROFITABLE - Even with fees, slippage, and uncertainty")
            print("  💰 Ready to launch in real markets")
        elif metrics['win_rate'] >= 50 and expected_value > 0:
            print("  ⚠️  MARGINAL - Barely profitable after costs")
            print("  🔧 May need higher win rate or better R:R")
        else:
            print("  ❌ UNPROFITABLE - Fees and slippage eat profits")
            print("  🔧 Needs optimization or different approach")

        print("="*60)


def main():
    """Run realistic backtest"""
    print("="*60)
    print("🔬 REALISTIC BACKTEST - WORST CASE SCENARIO")
    print("="*60)
    print("\nSimulating real trading conditions:")
    print("  • Market slippage on entries")
    print("  • Trading fees (0.2% round-trip)")
    print("  • Stop loss slippage (worse fills)")
    print("  • Partial fills (missed entries)")
    print("  • Random volatility spikes")
    print("\nThis shows ACTUAL expected performance.\n")

    backtester = RealisticBacktester(initial_capital=10000)

    test_symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'XRP/USDT', 'ADA/USDT']

    for symbol in test_symbols:
        try:
            backtester.backtest_symbol(symbol, days=365)
        except Exception as e:
            print(f"  ✗ Error: {e}")
            continue

    if backtester.trades:
        metrics = backtester.calculate_metrics()
        backtester.print_report(metrics)

        trades_df = pd.DataFrame(backtester.trades)
        output_file = "/tmp/realistic_backtest_results.csv"
        trades_df.to_csv(output_file, index=False)
        print(f"\n💾 Results saved to: {output_file}")
    else:
        print("\n❌ No trades found")


if __name__ == "__main__":
    main()
