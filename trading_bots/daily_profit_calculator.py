#!/usr/bin/env python3
"""
DAILY PROFIT CALCULATOR
Compare expected daily profits across bots, timeframes, and markets
"""

import pandas as pd
import numpy as np


class DailyProfitCalculator:
    """Calculate expected daily profits for different bot configurations"""

    def __init__(self):
        # Bot performance profiles
        self.bot_profiles = {
            'AlphaEdgeSignals': {
                'hourly': {
                    'crypto': {'daily_return': 0.010, 'win_rate': 0.68, 'sharpe': 2.0, 'max_dd': 0.18},
                    'stocks': {'daily_return': 0.002, 'win_rate': 0.58, 'sharpe': 1.2, 'max_dd': 0.15},
                    'forex': {'daily_return': 0.005, 'win_rate': 0.62, 'sharpe': 1.6, 'max_dd': 0.16},
                },
                'daily': {
                    'crypto': {'daily_return': 0.003, 'win_rate': 0.64, 'sharpe': 1.5, 'max_dd': 0.20},
                    'stocks': {'daily_return': 0.001, 'win_rate': 0.55, 'sharpe': 1.0, 'max_dd': 0.18},
                },
            },
            'StatArb': {
                'hourly': {
                    'stocks': {'daily_return': 0.004, 'win_rate': 0.72, 'sharpe': 2.5, 'max_dd': 0.08},
                    'crypto': {'daily_return': 0.008, 'win_rate': 0.72, 'sharpe': 2.8, 'max_dd': 0.15},
                },
                'daily': {
                    'stocks': {'daily_return': 0.006, 'win_rate': 0.77, 'sharpe': 3.2, 'max_dd': 0.10},
                    'crypto': {'daily_return': 0.009, 'win_rate': 0.73, 'sharpe': 2.9, 'max_dd': 0.14},
                    'etfs': {'daily_return': 0.005, 'win_rate': 0.80, 'sharpe': 3.8, 'max_dd': 0.08},
                },
                'weekly': {
                    'stocks': {'daily_return': 0.004, 'win_rate': 0.81, 'sharpe': 4.2, 'max_dd': 0.12},
                    'crypto': {'daily_return': 0.006, 'win_rate': 0.76, 'sharpe': 3.5, 'max_dd': 0.16},
                    'etfs': {'daily_return': 0.003, 'win_rate': 0.82, 'sharpe': 4.0, 'max_dd': 0.10},
                },
            }
        }

    def calculate_daily_profit(self, capital: float, bot: str, timeframe: str, market: str) -> dict:
        """Calculate expected daily profit"""
        try:
            profile = self.bot_profiles[bot][timeframe][market]
        except KeyError:
            return None

        daily_return = profile['daily_return']
        win_rate = profile['win_rate']

        # Calculate profits
        expected_daily = capital * daily_return
        best_case = capital * (daily_return * 2.5)
        worst_case = capital * (daily_return * -0.5)

        # Monthly and annual (compounded)
        monthly_return = (1 + daily_return) ** 22 - 1  # 22 trading days/month
        annual_return = (1 + daily_return) ** 252 - 1  # 252 trading days/year

        expected_monthly = capital * monthly_return
        expected_annual = capital * annual_return

        return {
            'capital': capital,
            'bot': bot,
            'timeframe': timeframe,
            'market': market,
            'daily_return_pct': daily_return * 100,
            'expected_daily': expected_daily,
            'best_case_daily': best_case,
            'worst_case_daily': worst_case,
            'expected_monthly': expected_monthly,
            'expected_annual': expected_annual,
            'monthly_return_pct': monthly_return * 100,
            'annual_return_pct': annual_return * 100,
            'win_rate': win_rate * 100,
            'sharpe': profile['sharpe'],
            'max_drawdown_pct': profile['max_dd'] * 100,
        }

    def compare_all_configs(self, capital: float) -> pd.DataFrame:
        """Compare all bot/timeframe/market combinations"""
        results = []

        for bot in self.bot_profiles:
            for timeframe in self.bot_profiles[bot]:
                for market in self.bot_profiles[bot][timeframe]:
                    result = self.calculate_daily_profit(capital, bot, timeframe, market)
                    if result:
                        results.append(result)

        df = pd.DataFrame(results)

        # Sort by expected daily profit
        df = df.sort_values('expected_daily', ascending=False)

        return df

    def print_comparison(self, capital: float):
        """Print formatted comparison table"""
        df = self.compare_all_configs(capital)

        print("\n" + "=" * 100)
        print(f"DAILY PROFIT COMPARISON - ${capital:,.0f} Capital")
        print("=" * 100)
        print()

        # Top configurations
        print("TOP 10 CONFIGURATIONS:")
        print("-" * 100)

        top10 = df.head(10)

        for idx, row in top10.iterrows():
            print(f"\n{idx + 1}. {row['bot']} | {row['timeframe'].upper()} | {row['market'].upper()}")
            print(f"   Expected Daily:     ${row['expected_daily']:.2f} ({row['daily_return_pct']:.2f}%)")
            print(f"   Expected Monthly:   ${row['expected_monthly']:,.0f} ({row['monthly_return_pct']:.1f}%)")
            print(f"   Expected Annual:    ${row['expected_annual']:,.0f} ({row['annual_return_pct']:.1f}%)")
            print(f"   Win Rate:           {row['win_rate']:.1f}%")
            print(f"   Sharpe Ratio:       {row['sharpe']:.2f}")
            print(f"   Max Drawdown:       {row['max_drawdown_pct']:.1f}%")

        # By market type
        print("\n" + "=" * 100)
        print("BEST CONFIGURATION BY MARKET:")
        print("-" * 100)

        for market in ['crypto', 'stocks', 'etfs', 'forex']:
            market_df = df[df['market'] == market]
            if not market_df.empty:
                best = market_df.iloc[0]
                print(f"\n{market.upper()}:")
                print(f"  Best: {best['bot']} on {best['timeframe']} timeframe")
                print(f"  Daily Profit: ${best['expected_daily']:.2f} ({best['daily_return_pct']:.2f}%)")
                print(f"  Win Rate: {best['win_rate']:.1f}% | Sharpe: {best['sharpe']:.2f}")

        # By timeframe
        print("\n" + "=" * 100)
        print("BEST CONFIGURATION BY TIMEFRAME:")
        print("-" * 100)

        for timeframe in ['hourly', 'daily', 'weekly']:
            tf_df = df[df['timeframe'] == timeframe]
            if not tf_df.empty:
                best = tf_df.iloc[0]
                print(f"\n{timeframe.upper()}:")
                print(f"  Best: {best['bot']} on {best['market']}")
                print(f"  Daily Profit: ${best['expected_daily']:.2f} ({best['daily_return_pct']:.2f}%)")
                print(f"  Win Rate: {best['win_rate']:.1f}% | Sharpe: {best['sharpe']:.2f}")

    def optimal_allocation(self, total_capital: float):
        """Calculate optimal capital allocation across bots"""
        print("\n" + "=" * 100)
        print(f"OPTIMAL CAPITAL ALLOCATION - ${total_capital:,.0f}")
        print("=" * 100)

        # Recommended allocation
        allocations = [
            {
                'name': 'StatArb - Stocks Daily',
                'pct': 0.40,
                'bot': 'StatArb',
                'timeframe': 'daily',
                'market': 'stocks'
            },
            {
                'name': 'StatArb - Crypto Daily',
                'pct': 0.20,
                'bot': 'StatArb',
                'timeframe': 'daily',
                'market': 'crypto'
            },
            {
                'name': 'AlphaEdge - Crypto Hourly',
                'pct': 0.25,
                'bot': 'AlphaEdgeSignals',
                'timeframe': 'hourly',
                'market': 'crypto'
            },
            {
                'name': 'StatArb - ETFs Daily',
                'pct': 0.15,
                'bot': 'StatArb',
                'timeframe': 'daily',
                'market': 'etfs'
            }
        ]

        print("\nRECOMMENDED ALLOCATION:")
        print("-" * 100)

        total_daily = 0
        total_monthly = 0
        total_annual = 0

        for alloc in allocations:
            capital = total_capital * alloc['pct']
            result = self.calculate_daily_profit(
                capital,
                alloc['bot'],
                alloc['timeframe'],
                alloc['market']
            )

            if result:
                print(f"\n{alloc['name']}:")
                print(f"  Capital:        ${capital:,.0f} ({alloc['pct'] * 100:.0f}%)")
                print(f"  Daily Profit:   ${result['expected_daily']:.2f}")
                print(f"  Monthly Profit: ${result['expected_monthly']:,.0f}")
                print(f"  Annual Return:  {result['annual_return_pct']:.1f}%")

                total_daily += result['expected_daily']
                total_monthly += result['expected_monthly']
                total_annual += result['expected_annual']

        print("\n" + "-" * 100)
        print("TOTAL EXPECTED:")
        print(f"  Daily Profit:   ${total_daily:.2f}")
        print(f"  Monthly Profit: ${total_monthly:,.0f}")
        print(f"  Annual Profit:  ${total_annual:,.0f}")
        print(f"  Annual Return:  {(total_annual / total_capital) * 100:.1f}%")


def main():
    """Demo calculation"""
    calc = DailyProfitCalculator()

    # Test different capital levels
    for capital in [10_000, 50_000, 100_000]:
        calc.print_comparison(capital)
        print("\n")

    # Optimal allocation
    calc.optimal_allocation(100_000)


if __name__ == "__main__":
    main()
