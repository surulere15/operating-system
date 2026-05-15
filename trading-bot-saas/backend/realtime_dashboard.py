"""
REAL-TIME MONITORING DASHBOARD
Live performance tracking and visualization for 474% monthly target

Features:
- Real-time P&L tracking
- Per-strategy performance metrics
- Risk monitoring and alerts
- Target progress visualization
- Circuit breaker status
"""

import time
import os
from datetime import datetime, timedelta
from typing import Dict, Any
from collections import deque
import numpy as np


class RealtimeDashboard:
    """
    Real-time monitoring dashboard for multi-strategy trading system

    Displays:
    - Current capital and P&L
    - Daily/monthly progress vs 474% target
    - Per-strategy performance
    - Risk metrics and alerts
    - Trade history
    """

    def __init__(self, target_monthly_return: float = 4.74, refresh_interval: int = 1):
        self.target_monthly_return = target_monthly_return  # 474%
        self.target_daily_return = 0.0639  # 6.39% daily for 474% monthly
        self.refresh_interval = refresh_interval

        # Performance history (ring buffers)
        self.capital_history = deque(maxlen=1000)
        self.pnl_history = deque(maxlen=1000)
        self.recent_trades = deque(maxlen=50)

        # Alert thresholds
        self.alert_thresholds = {
            'daily_loss_warning': -0.05,  # -5% daily
            'daily_loss_critical': -0.10,  # -10% daily
            'win_rate_warning': 0.50,  # Win rate below 50%
            'latency_warning': 100,  # Latency > 100ms
            'spread_warning': 0.05  # Spread > 0.05%
        }

        self.active_alerts = []

    def clear_screen(self):
        """Clear terminal screen"""
        os.system('clear' if os.name == 'posix' else 'cls')

    def render(self, orchestrator_status: Dict[str, Any], ws_stats: Dict[str, Any] = None):
        """Render the dashboard"""
        self.clear_screen()

        # Header
        self._render_header()

        # Capital & P&L
        self._render_capital(orchestrator_status)

        # Target Progress
        self._render_target_progress(orchestrator_status)

        # Strategy Performance
        self._render_strategies(orchestrator_status)

        # Risk Metrics
        self._render_risk(orchestrator_status)

        # WebSocket Stats (if available)
        if ws_stats:
            self._render_websocket_stats(ws_stats)

        # Recent Trades
        self._render_recent_trades()

        # Alerts
        self._render_alerts()

        # Footer
        self._render_footer()

    def _render_header(self):
        """Render dashboard header"""
        print("═" * 100)
        print(f"{'🚀 AGGRESSIVE TRADING SYSTEM - REAL-TIME DASHBOARD':^100}")
        print(f"{'Target: $500 → $2,872 in 30 days (+474%)':^100}")
        print("═" * 100)
        print(f"Last Update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

    def _render_capital(self, status: Dict[str, Any]):
        """Render capital and P&L section"""
        capital = status['capital']

        print("┌" + "─" * 98 + "┐")
        print("│" + " 💰 CAPITAL & P&L".ljust(98) + "│")
        print("├" + "─" * 98 + "┤")

        # Build the rows
        initial_str = f"Initial: ${capital['initial']:>12,.2f}"
        current_str = f"Current: ${capital['current']:>12,.2f}"
        peak_str = f"Peak: ${capital['peak']:>12,.2f}"

        total_pnl_emoji = "📈" if capital['total_pnl'] >= 0 else "📉"
        daily_pnl_emoji = "⬆️" if capital['daily_pnl'] >= 0 else "⬇️"

        total_pnl_str = f"{total_pnl_emoji} Total P&L: ${capital['total_pnl']:>+12,.2f} ({capital['total_return_pct']:>+7.2f}%)"
        daily_pnl_str = f"{daily_pnl_emoji} Daily P&L: ${capital['daily_pnl']:>+12,.2f} ({capital['daily_return_pct']:>+7.2f}%)"

        print(f"│  {initial_str:<30} {current_str:<30} {peak_str:<35}│")
        print(f"│  {total_pnl_str:<48} {daily_pnl_str:<48}│")
        print("└" + "─" * 98 + "┘")
        print()

    def _render_target_progress(self, status: Dict[str, Any]):
        """Render target progress section"""
        target = status['target']

        print("┌" + "─" * 98 + "┐")
        print("│" + " 🎯 TARGET PROGRESS (474% MONTHLY)".ljust(98) + "│")
        print("├" + "─" * 98 + "┤")

        # Daily target
        daily_target = self.target_daily_return * 100
        daily_actual = target['daily_progress_pct']
        daily_diff = daily_actual - daily_target

        on_track_emoji = "✅" if target['on_track'] else "❌"
        progress_emoji = "🟢" if daily_diff >= 0 else "🔴"

        daily_status = f"Daily Target: {daily_target:.2f}% | Actual: {daily_actual:+.2f}% | Diff: {progress_emoji} {daily_diff:+.2f}%"
        on_track_status = f"{on_track_emoji} On Track: {'YES' if target['on_track'] else 'NO'}"

        # Progress bar
        if daily_target > 0:
            progress_pct = min(100, (daily_actual / daily_target) * 100) if daily_actual > 0 else 0
        else:
            progress_pct = 0

        bar_length = 60
        filled = int((progress_pct / 100) * bar_length)
        bar = "█" * filled + "░" * (bar_length - filled)
        progress_bar = f"Progress: [{bar}] {progress_pct:.1f}%"

        # Monthly projection
        monthly_proj = target['monthly_projection']
        monthly_status = f"Monthly Projection: {monthly_proj:.1f}% (Target: 474%)"

        elapsed = target['elapsed_days']
        elapsed_status = f"Elapsed: {elapsed:.1f} days | Remaining: {30 - elapsed:.1f} days"

        print(f"│  {daily_status:<96}│")
        print(f"│  {on_track_status:<96}│")
        print(f"│  {progress_bar:<96}│")
        print(f"│  {monthly_status:<96}│")
        print(f"│  {elapsed_status:<96}│")
        print("└" + "─" * 98 + "┘")
        print()

    def _render_strategies(self, status: Dict[str, Any]):
        """Render per-strategy performance"""
        print("┌" + "─" * 98 + "┐")
        print("│" + " 📈 STRATEGY PERFORMANCE".ljust(98) + "│")
        print("├" + "─" * 98 + "┤")

        # Header
        header = f"│  {'Strategy':<25} {'Status':<10} {'Trades':<8} {'Win%':<8} {'P&L':<15} {'Daily P&L':<15}│"
        print(header)
        print("├" + "─" * 98 + "┤")

        strategies = status['strategies']

        # Strategy display names
        display_names = {
            'hf_scalping': 'HF Scalping (20x)',
            'momentum': 'Momentum Breakout (15x)',
            'stat_arb': 'Stat Arbitrage (12x)',
            'funding_arb': 'Funding Arb (10x)',
            'grid': 'Grid Trading (8x)'
        }

        for strategy_key, strategy_data in strategies.items():
            name = display_names.get(strategy_key, strategy_key)

            # Status emoji
            status_emoji = {
                'active': '🟢',
                'paused': '🟡',
                'stopped': '🔴',
                'error': '💥'
            }.get(strategy_data['status'], '⚪')

            status_str = f"{status_emoji} {strategy_data['status'].upper()}"

            # Metrics
            trades = strategy_data['trades']
            win_rate = strategy_data['win_rate'] * 100
            pnl = strategy_data['pnl']
            daily_pnl = strategy_data['daily_pnl']

            # Color coding for P&L
            pnl_emoji = "📈" if pnl >= 0 else "📉"
            daily_emoji = "⬆️" if daily_pnl >= 0 else "⬇️"

            pnl_str = f"{pnl_emoji} ${pnl:+.2f}"
            daily_pnl_str = f"{daily_emoji} ${daily_pnl:+.2f}"

            row = f"│  {name:<25} {status_str:<12} {trades:<8} {win_rate:<7.1f}% {pnl_str:<17} {daily_pnl_str:<15}│"
            print(row)

        # Totals
        total_trades = status['trades']['total']
        total_wins = status['trades']['total_wins']
        total_losses = status['trades']['total_losses']
        overall_wr = status['trades']['overall_win_rate'] * 100

        print("├" + "─" * 98 + "┤")
        totals = f"│  {'TOTAL':<25} {'':<12} {total_trades:<8} {overall_wr:<7.1f}% (W:{total_wins} L:{total_losses})"
        print(f"{totals:<99}│")
        print("└" + "─" * 98 + "┘")
        print()

    def _render_risk(self, status: Dict[str, Any]):
        """Render risk metrics"""
        print("┌" + "─" * 98 + "┐")
        print("│" + " ⚠️  RISK METRICS".ljust(98) + "│")
        print("├" + "─" * 98 + "┤")

        risk = status['risk']

        # Circuit breaker
        cb_status = "🚨 ACTIVE" if risk['circuit_breaker_active'] else "✅ OK"
        cb_reason = risk['circuit_breaker_reason'] if risk['circuit_breaker_active'] else "N/A"

        cb_str = f"Circuit Breaker: {cb_status}"
        if risk['circuit_breaker_active']:
            cb_str += f" | Reason: {cb_reason}"

        # Drawdown
        drawdown = risk['drawdown_pct']
        dd_emoji = "🔴" if drawdown > 10 else "🟡" if drawdown > 5 else "🟢"
        dd_str = f"Drawdown: {dd_emoji} {drawdown:.2f}%"

        # Daily loss tracking
        daily_pnl = status['capital']['daily_pnl']
        daily_loss_pct = (daily_pnl / status['capital']['initial']) * 100 if daily_pnl < 0 else 0

        loss_emoji = "🔴" if daily_loss_pct < -10 else "🟡" if daily_loss_pct < -5 else "🟢"
        loss_str = f"Daily Loss: {loss_emoji} {daily_loss_pct:.2f}%"

        print(f"│  {cb_str:<96}│")
        print(f"│  {dd_str:<50} {loss_str:<45}│")
        print("└" + "─" * 98 + "┘")
        print()

    def _render_websocket_stats(self, ws_stats: Dict[str, Any]):
        """Render WebSocket connection stats"""
        print("┌" + "─" * 98 + "┐")
        print("│" + " 📡 WEBSOCKET CONNECTION".ljust(98) + "│")
        print("├" + "─" * 98 + "┤")

        latency_avg = ws_stats.get('avg_ms', 0)
        latency_emoji = "🟢" if latency_avg < 50 else "🟡" if latency_avg < 100 else "🔴"

        latency_str = f"Latency: {latency_emoji} Avg: {latency_avg:.2f}ms | Min: {ws_stats.get('min_ms', 0):.2f}ms | Max: {ws_stats.get('max_ms', 0):.2f}ms"

        print(f"│  {latency_str:<96}│")
        print("└" + "─" * 98 + "┘")
        print()

    def _render_recent_trades(self):
        """Render recent trades"""
        if len(self.recent_trades) == 0:
            return

        print("┌" + "─" * 98 + "┐")
        print("│" + " 📊 RECENT TRADES (Last 10)".ljust(98) + "│")
        print("├" + "─" * 98 + "┤")

        # Header
        header = f"│  {'Time':<12} {'Strategy':<20} {'Side':<6} {'Result':<6} {'P&L':<12} {'Balance':<15}│"
        print(header)
        print("├" + "─" * 98 + "┤")

        # Show last 10 trades
        recent = list(self.recent_trades)[-10:]
        for trade in recent:
            time_str = trade['time'].strftime('%H:%M:%S')
            strategy_str = trade['strategy'][:18]
            side_str = trade['side'].upper()
            result_emoji = "✅" if trade['is_win'] else "❌"
            pnl_str = f"${trade['pnl']:+.2f}"
            balance_str = f"${trade['balance']:,.2f}"

            row = f"│  {time_str:<12} {strategy_str:<20} {side_str:<6} {result_emoji:<8} {pnl_str:<12} {balance_str:<15}│"
            print(row)

        print("└" + "─" * 98 + "┘")
        print()

    def _render_alerts(self):
        """Render active alerts"""
        if len(self.active_alerts) == 0:
            return

        print("┌" + "─" * 98 + "┐")
        print("│" + " 🚨 ACTIVE ALERTS".ljust(98) + "│")
        print("├" + "─" * 98 + "┤")

        for alert in self.active_alerts[-5:]:  # Show last 5 alerts
            print(f"│  {alert:<96}│")

        print("└" + "─" * 98 + "┘")
        print()

    def _render_footer(self):
        """Render dashboard footer"""
        print("═" * 100)
        print(f"Next refresh in {self.refresh_interval} second(s) | Press Ctrl+C to exit")
        print("═" * 100)

    def add_trade(self, strategy: str, side: str, is_win: bool, pnl: float, balance: float):
        """Add a trade to recent trades"""
        self.recent_trades.append({
            'time': datetime.now(),
            'strategy': strategy,
            'side': side,
            'is_win': is_win,
            'pnl': pnl,
            'balance': balance
        })

    def add_alert(self, alert_message: str):
        """Add an alert"""
        timestamped = f"[{datetime.now().strftime('%H:%M:%S')}] {alert_message}"
        self.active_alerts.append(timestamped)

    def check_alerts(self, status: Dict[str, Any], ws_stats: Dict[str, Any] = None):
        """Check for alert conditions"""

        # Daily loss warning
        daily_return_pct = status['capital']['daily_return_pct'] / 100
        if daily_return_pct <= self.alert_thresholds['daily_loss_warning']:
            self.add_alert(f"⚠️ Daily loss {daily_return_pct*100:.1f}% exceeds warning threshold")

        # Daily loss critical
        if daily_return_pct <= self.alert_thresholds['daily_loss_critical']:
            self.add_alert(f"🚨 CRITICAL: Daily loss {daily_return_pct*100:.1f}% exceeds critical threshold")

        # Win rate warning
        overall_wr = status['trades']['overall_win_rate']
        if overall_wr < self.alert_thresholds['win_rate_warning'] and status['trades']['total'] >= 10:
            self.add_alert(f"⚠️ Win rate {overall_wr*100:.1f}% below threshold")

        # Latency warning
        if ws_stats and ws_stats.get('avg_ms', 0) > self.alert_thresholds['latency_warning']:
            self.add_alert(f"⚠️ High latency: {ws_stats['avg_ms']:.1f}ms")

        # Circuit breaker
        if status['risk']['circuit_breaker_active']:
            self.add_alert(f"🚨 CIRCUIT BREAKER TRIGGERED: {status['risk']['circuit_breaker_reason']}")


# Example usage
if __name__ == '__main__':
    # Mock data for testing
    mock_status = {
        'capital': {
            'initial': 500,
            'current': 532.50,
            'peak': 545.20,
            'total_pnl': 32.50,
            'total_return_pct': 6.50,
            'daily_pnl': 18.30,
            'daily_return_pct': 3.66
        },
        'trades': {
            'total': 15,
            'total_wins': 11,
            'total_losses': 4,
            'overall_win_rate': 0.733
        },
        'strategies': {
            'hf_scalping': {'status': 'active', 'trades': 5, 'win_rate': 0.80, 'pnl': 12.50, 'daily_pnl': 8.20},
            'momentum': {'status': 'active', 'trades': 3, 'win_rate': 0.67, 'pnl': 8.40, 'daily_pnl': 5.10},
            'stat_arb': {'status': 'active', 'trades': 4, 'win_rate': 0.75, 'pnl': 10.20, 'daily_pnl': 4.50},
            'funding_arb': {'status': 'active', 'trades': 1, 'win_rate': 1.00, 'pnl': 0.80, 'daily_pnl': 0.30},
            'grid': {'status': 'active', 'trades': 2, 'win_rate': 0.50, 'pnl': 0.60, 'daily_pnl': 0.20}
        },
        'risk': {
            'circuit_breaker_active': False,
            'circuit_breaker_reason': None,
            'drawdown_pct': 2.35
        },
        'target': {
            'daily_target_pct': 6.39,
            'daily_progress_pct': 3.66,
            'on_track': False,
            'elapsed_days': 0.5,
            'monthly_projection': 245.8
        }
    }

    mock_ws_stats = {
        'min_ms': 12.5,
        'max_ms': 45.2,
        'avg_ms': 24.8,
        'samples': 150
    }

    dashboard = RealtimeDashboard()

    # Add some mock trades
    dashboard.add_trade('HF Scalping', 'long', True, 2.50, 532.50)
    dashboard.add_trade('Momentum', 'short', True, 3.20, 529.00)
    dashboard.add_trade('Stat Arb', 'long', False, -1.50, 525.80)

    # Render
    dashboard.render(mock_status, mock_ws_stats)
    dashboard.check_alerts(mock_status, mock_ws_stats)
