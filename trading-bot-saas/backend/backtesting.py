"""
Backtesting Engine
Test trading strategies on historical data before going live
"""

import ccxt
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import logging
from strategies import StrategyFactory

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BacktestEngine:
    """
    Backtesting engine to simulate trading strategies on historical data

    Features:
    - Historical data simulation
    - Realistic trade execution (slippage, fees)
    - Risk management simulation
    - Performance metrics calculation
    """

    def __init__(self, exchange_name: str, symbol: str, strategy_name: str, config: Dict):
        """
        Initialize backtest engine

        Args:
            exchange_name: Exchange to fetch data from (e.g., 'bybit')
            symbol: Trading pair (e.g., 'BTC/USDT')
            strategy_name: Strategy to test ('ma_crossover', 'grid', 'dca', 'macd')
            config: Strategy and backtest configuration
        """
        self.exchange_name = exchange_name
        self.symbol = symbol
        self.config = config

        # Initialize exchange (public API only, no auth needed)
        exchange_class = getattr(ccxt, exchange_name.lower())
        self.exchange = exchange_class({
            'enableRateLimit': True,
            'options': {'defaultType': 'future'}
        })

        # Initialize strategy
        self.strategy = StrategyFactory.create_strategy(strategy_name, config)

        # Backtest parameters
        self.initial_capital = config.get('capital', 100)
        self.leverage = config.get('default_leverage', 15)
        self.fee_rate = config.get('fee_rate', 0.001)  # 0.1% trading fee
        self.slippage = config.get('slippage', 0.0005)  # 0.05% slippage

        # Risk management
        self.max_daily_loss = config.get('max_daily_loss', 10)  # %
        self.max_position_loss = config.get('max_position_loss', 3)  # %
        self.position_size_percent = config.get('position_size_percent', 20)  # % of capital per trade

        # State tracking
        self.current_capital = self.initial_capital
        self.trades = []
        self.equity_curve = []
        self.daily_pnl = {}

    def fetch_historical_data(self, timeframe: str, days: int) -> List:
        """
        Fetch historical OHLCV data

        Args:
            timeframe: Candle timeframe ('15m', '1h', '4h', '1d')
            days: Number of days of historical data

        Returns:
            List of OHLCV candles
        """
        try:
            # Calculate number of candles needed
            timeframe_minutes = {
                '1m': 1, '5m': 5, '15m': 15, '30m': 30,
                '1h': 60, '4h': 240, '1d': 1440
            }
            minutes_per_candle = timeframe_minutes.get(timeframe, 15)
            total_candles = (days * 24 * 60) // minutes_per_candle

            # Fetch in batches (max 1000 per request)
            all_data = []
            batch_size = 1000

            for i in range(0, total_candles, batch_size):
                since = self.exchange.milliseconds() - ((total_candles - i) * minutes_per_candle * 60 * 1000)
                data = self.exchange.fetch_ohlcv(
                    self.symbol,
                    timeframe=timeframe,
                    since=since,
                    limit=min(batch_size, total_candles - i)
                )
                all_data.extend(data)

            logger.info(f"📊 Fetched {len(all_data)} candles ({days} days, {timeframe})")
            return all_data

        except Exception as e:
            logger.error(f"❌ Failed to fetch historical data: {str(e)}")
            raise

    def calculate_position_size(self, price: float) -> float:
        """Calculate position size based on capital and leverage"""
        capital_for_trade = self.current_capital * (self.position_size_percent / 100)
        position_value = capital_for_trade * self.leverage
        quantity = position_value / price
        return quantity

    def simulate_trade(self, action: str, entry_price: float, timestamp: int) -> Dict:
        """
        Simulate opening a trade

        Returns:
            Trade dict with entry details
        """
        # Apply slippage
        if action == 'buy':
            actual_entry = entry_price * (1 + self.slippage)
        else:  # sell
            actual_entry = entry_price * (1 - self.slippage)

        # Calculate position size
        quantity = self.calculate_position_size(actual_entry)

        # Calculate stop loss and take profit
        if action == 'buy':
            stop_loss = actual_entry * (1 - self.max_position_loss / 100)
            take_profit = actual_entry * (1 + 0.05)  # 5% profit target
        else:  # sell
            stop_loss = actual_entry * (1 + self.max_position_loss / 100)
            take_profit = actual_entry * (1 - 0.05)

        # Calculate fees
        position_value = actual_entry * quantity
        entry_fee = position_value * self.fee_rate

        trade = {
            'action': action,
            'entry_price': actual_entry,
            'quantity': quantity,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'entry_timestamp': timestamp,
            'entry_fee': entry_fee,
            'status': 'open',
            'exit_price': None,
            'exit_timestamp': None,
            'exit_fee': None,
            'pnl': None,
            'pnl_percent': None,
            'exit_reason': None
        }

        return trade

    def check_exit_conditions(self, trade: Dict, current_price: float, timestamp: int) -> Tuple[bool, str]:
        """
        Check if trade should be closed

        Returns:
            (should_exit: bool, reason: str)
        """
        if trade['status'] != 'open':
            return False, ''

        # Check stop loss
        if trade['action'] == 'buy':
            if current_price <= trade['stop_loss']:
                return True, 'stop_loss'
            if current_price >= trade['take_profit']:
                return True, 'take_profit'
        else:  # sell
            if current_price >= trade['stop_loss']:
                return True, 'stop_loss'
            if current_price <= trade['take_profit']:
                return True, 'take_profit'

        return False, ''

    def close_trade(self, trade: Dict, exit_price: float, timestamp: int, reason: str):
        """Close a trade and calculate P&L"""
        # Apply slippage
        if trade['action'] == 'buy':
            actual_exit = exit_price * (1 - self.slippage)
        else:  # sell
            actual_exit = exit_price * (1 + self.slippage)

        # Calculate P&L
        if trade['action'] == 'buy':
            pnl = (actual_exit - trade['entry_price']) * trade['quantity'] * self.leverage
        else:  # sell
            pnl = (trade['entry_price'] - actual_exit) * trade['quantity'] * self.leverage

        # Subtract fees
        exit_fee = actual_exit * trade['quantity'] * self.fee_rate
        pnl -= (trade['entry_fee'] + exit_fee)

        # Calculate P&L percentage
        position_value = trade['entry_price'] * trade['quantity']
        pnl_percent = (pnl / position_value) * 100

        # Update trade
        trade['exit_price'] = actual_exit
        trade['exit_timestamp'] = timestamp
        trade['exit_fee'] = exit_fee
        trade['pnl'] = pnl
        trade['pnl_percent'] = pnl_percent
        trade['status'] = 'closed'
        trade['exit_reason'] = reason

        # Update capital
        self.current_capital += pnl

        # Track daily P&L
        date = datetime.fromtimestamp(timestamp / 1000).date()
        if date not in self.daily_pnl:
            self.daily_pnl[date] = 0
        self.daily_pnl[date] += pnl

        return trade

    def check_daily_loss_limit(self, timestamp: int) -> bool:
        """Check if daily loss limit has been hit"""
        date = datetime.fromtimestamp(timestamp / 1000).date()
        daily_loss = self.daily_pnl.get(date, 0)
        daily_loss_percent = (daily_loss / self.initial_capital) * 100

        return daily_loss_percent <= -self.max_daily_loss

    def run_backtest(self, timeframe: str = '15m', days: int = 30) -> Dict:
        """
        Run backtest simulation

        Args:
            timeframe: Candle timeframe
            days: Number of days to backtest

        Returns:
            Backtest results with performance metrics
        """
        try:
            logger.info(f"🔄 Starting backtest: {self.symbol} | {self.strategy.__class__.__name__} | {days} days")

            # Fetch historical data
            historical_data = self.fetch_historical_data(timeframe, days)

            if len(historical_data) < 100:
                raise ValueError("Insufficient historical data")

            # Reset state
            self.current_capital = self.initial_capital
            self.trades = []
            self.equity_curve = []
            self.daily_pnl = {}

            open_trade = None

            # Iterate through historical data
            for i in range(100, len(historical_data)):  # Need 100 candles for indicators
                candles = historical_data[max(0, i-100):i+1]
                current_candle = historical_data[i]
                current_price = current_candle[4]  # Close price
                timestamp = current_candle[0]

                # Record equity
                self.equity_curve.append({
                    'timestamp': timestamp,
                    'equity': self.current_capital
                })

                # Check if daily loss limit hit
                if self.check_daily_loss_limit(timestamp):
                    logger.info(f"⚠️ Daily loss limit hit at {datetime.fromtimestamp(timestamp/1000)}")
                    if open_trade:
                        self.close_trade(open_trade, current_price, timestamp, 'daily_loss_limit')
                        self.trades.append(open_trade)
                        open_trade = None
                    continue

                # Check open trade exit conditions
                if open_trade:
                    should_exit, reason = self.check_exit_conditions(open_trade, current_price, timestamp)
                    if should_exit:
                        self.close_trade(open_trade, current_price, timestamp, reason)
                        self.trades.append(open_trade)
                        open_trade = None

                # Generate signal if no open trade
                if not open_trade:
                    signal = self.strategy.generate_signal(candles, current_price)

                    # Execute trade if signal is strong enough
                    confidence_threshold = self.config.get('confidence_threshold', 60)
                    if signal['action'] in ['buy', 'sell'] and signal['confidence'] >= confidence_threshold:
                        open_trade = self.simulate_trade(signal['action'], current_price, timestamp)

            # Close any remaining open trade
            if open_trade:
                last_candle = historical_data[-1]
                self.close_trade(open_trade, last_candle[4], last_candle[0], 'backtest_end')
                self.trades.append(open_trade)

            # Calculate performance metrics
            results = self.calculate_metrics()

            logger.info(f"✅ Backtest complete: {len(self.trades)} trades, {results['win_rate']:.1f}% win rate, {results['total_pnl']:.2f} P&L")

            return results

        except Exception as e:
            logger.error(f"❌ Backtest failed: {str(e)}")
            raise

    def calculate_metrics(self) -> Dict:
        """Calculate comprehensive performance metrics"""
        closed_trades = [t for t in self.trades if t['status'] == 'closed']

        if not closed_trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'total_pnl': 0,
                'total_pnl_percent': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'best_trade': 0,
                'worst_trade': 0,
                'profit_factor': 0,
                'max_drawdown': 0,
                'sharpe_ratio': 0,
                'trades': [],
                'equity_curve': []
            }

        # Basic metrics
        total_trades = len(closed_trades)
        winning_trades = [t for t in closed_trades if t['pnl'] > 0]
        losing_trades = [t for t in closed_trades if t['pnl'] <= 0]

        win_count = len(winning_trades)
        loss_count = len(losing_trades)
        win_rate = (win_count / total_trades * 100) if total_trades > 0 else 0

        # P&L metrics
        total_pnl = sum(t['pnl'] for t in closed_trades)
        total_pnl_percent = ((self.current_capital - self.initial_capital) / self.initial_capital) * 100

        avg_win = np.mean([t['pnl'] for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t['pnl'] for t in losing_trades]) if losing_trades else 0
        best_trade = max([t['pnl'] for t in closed_trades]) if closed_trades else 0
        worst_trade = min([t['pnl'] for t in closed_trades]) if closed_trades else 0

        # Profit factor
        gross_profit = sum(t['pnl'] for t in winning_trades) if winning_trades else 0
        gross_loss = abs(sum(t['pnl'] for t in losing_trades)) if losing_trades else 0
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else 0

        # Maximum drawdown
        max_drawdown = self._calculate_max_drawdown()

        # Sharpe ratio (simplified)
        sharpe_ratio = self._calculate_sharpe_ratio(closed_trades)

        # Average trade duration
        durations = [(t['exit_timestamp'] - t['entry_timestamp']) / 1000 / 3600 for t in closed_trades]  # hours
        avg_duration_hours = np.mean(durations) if durations else 0

        return {
            'total_trades': total_trades,
            'winning_trades': win_count,
            'losing_trades': loss_count,
            'win_rate': round(win_rate, 2),
            'total_pnl': round(total_pnl, 2),
            'total_pnl_percent': round(total_pnl_percent, 2),
            'avg_win': round(avg_win, 2),
            'avg_loss': round(avg_loss, 2),
            'best_trade': round(best_trade, 2),
            'worst_trade': round(worst_trade, 2),
            'profit_factor': round(profit_factor, 2),
            'max_drawdown': round(max_drawdown, 2),
            'max_drawdown_percent': round((max_drawdown / self.initial_capital) * 100, 2),
            'sharpe_ratio': round(sharpe_ratio, 2),
            'avg_duration_hours': round(avg_duration_hours, 2),
            'initial_capital': self.initial_capital,
            'final_capital': round(self.current_capital, 2),
            'trades': closed_trades,
            'equity_curve': self.equity_curve
        }

    def _calculate_max_drawdown(self) -> float:
        """Calculate maximum drawdown from equity curve"""
        if not self.equity_curve:
            return 0

        equity_values = [e['equity'] for e in self.equity_curve]
        peak = equity_values[0]
        max_dd = 0

        for equity in equity_values:
            if equity > peak:
                peak = equity
            dd = peak - equity
            if dd > max_dd:
                max_dd = dd

        return max_dd

    def _calculate_sharpe_ratio(self, trades: List[Dict], risk_free_rate: float = 0.02) -> float:
        """
        Calculate Sharpe ratio

        Args:
            trades: List of closed trades
            risk_free_rate: Annual risk-free rate (default 2%)

        Returns:
            Sharpe ratio
        """
        if not trades:
            return 0

        returns = [t['pnl_percent'] / 100 for t in trades]

        if len(returns) < 2:
            return 0

        avg_return = np.mean(returns)
        std_return = np.std(returns)

        if std_return == 0:
            return 0

        # Annualized Sharpe (assuming daily returns)
        sharpe = (avg_return - risk_free_rate / 365) / std_return * np.sqrt(365)

        return sharpe
