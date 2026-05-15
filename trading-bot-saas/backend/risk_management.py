"""
Advanced Risk Management System
Portfolio-level risk controls, VaR calculations, and exposure management

This is an INSTITUTIONAL-GRADE feature worth $200+/month on professional platforms
"""

import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from database import Bot, Trade, User
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RiskManager:
    """
    Advanced risk management for trading portfolios

    Features:
    - Value at Risk (VaR) calculations
    - Portfolio correlation analysis
    - Exposure limits and monitoring
    - Drawdown protection
    - Risk/Reward ratio analysis
    - Position sizing recommendations
    """

    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id

    def calculate_portfolio_risk(self) -> Dict:
        """
        Calculate comprehensive portfolio risk metrics

        Returns:
            Dictionary with risk metrics
        """
        try:
            # Get user's bots and trades
            bots = self.db.query(Bot).filter(Bot.user_id == self.user_id).all()

            if not bots:
                return self._empty_risk_metrics()

            # Calculate portfolio value
            total_value = sum(bot.current_balance for bot in bots)
            total_invested = sum(bot.capital for bot in bots)

            # Get all closed trades for analysis
            all_trades = []
            for bot in bots:
                trades = self.db.query(Trade).filter(
                    Trade.bot_id == bot.id,
                    Trade.status == 'closed',
                    Trade.pnl.isnot(None)
                ).all()
                all_trades.extend(trades)

            if not all_trades:
                return self._empty_risk_metrics()

            # Calculate metrics
            var_95 = self._calculate_var(all_trades, confidence=0.95)
            var_99 = self._calculate_var(all_trades, confidence=0.99)
            cvar_95 = self._calculate_cvar(all_trades, confidence=0.95)

            volatility = self._calculate_volatility(all_trades)
            sharpe = self._calculate_sharpe_ratio(all_trades, total_invested)
            sortino = self._calculate_sortino_ratio(all_trades, total_invested)

            max_drawdown = self._calculate_max_drawdown(all_trades, total_invested)
            current_drawdown = self._calculate_current_drawdown(bots)

            # Risk score (0-100, lower is better)
            risk_score = self._calculate_risk_score(
                var_95, volatility, max_drawdown, current_drawdown, total_value
            )

            # Position exposure
            exposure = self._calculate_exposure(bots)

            return {
                'total_value': round(total_value, 2),
                'total_invested': round(total_invested, 2),
                'total_pnl': round(total_value - total_invested, 2),
                'value_at_risk_95': round(var_95, 2),
                'value_at_risk_99': round(var_99, 2),
                'conditional_var_95': round(cvar_95, 2),
                'volatility': round(volatility, 2),
                'sharpe_ratio': round(sharpe, 2),
                'sortino_ratio': round(sortino, 2),
                'max_drawdown': round(max_drawdown, 2),
                'max_drawdown_percent': round((max_drawdown / total_invested * 100) if total_invested > 0 else 0, 2),
                'current_drawdown': round(current_drawdown, 2),
                'current_drawdown_percent': round((current_drawdown / total_value * 100) if total_value > 0 else 0, 2),
                'risk_score': round(risk_score, 1),
                'risk_level': self._get_risk_level(risk_score),
                'total_exposure': round(exposure['total'], 2),
                'exposure_by_exchange': exposure['by_exchange'],
                'exposure_by_symbol': exposure['by_symbol'],
                'total_trades': len(all_trades),
                'active_bots': len([b for b in bots if b.status == 'active'])
            }

        except Exception as e:
            logger.error(f"❌ Portfolio risk calculation failed: {str(e)}")
            return self._empty_risk_metrics()

    def _calculate_var(self, trades: List[Trade], confidence: float = 0.95) -> float:
        """
        Calculate Value at Risk (VaR) - maximum expected loss at given confidence level
        """
        if not trades:
            return 0

        returns = [trade.pnl for trade in trades]
        var = np.percentile(returns, (1 - confidence) * 100)
        return abs(var)

    def _calculate_cvar(self, trades: List[Trade], confidence: float = 0.95) -> float:
        """
        Calculate Conditional VaR (CVaR) - expected loss beyond VaR threshold
        """
        if not trades:
            return 0

        returns = [trade.pnl for trade in trades]
        var_threshold = np.percentile(returns, (1 - confidence) * 100)

        # Average of losses worse than VaR
        tail_losses = [r for r in returns if r <= var_threshold]
        cvar = abs(np.mean(tail_losses)) if tail_losses else 0

        return cvar

    def _calculate_volatility(self, trades: List[Trade]) -> float:
        """
        Calculate portfolio volatility (standard deviation of returns)
        """
        if len(trades) < 2:
            return 0

        returns = [trade.pnl for trade in trades]
        volatility = np.std(returns)

        return volatility

    def _calculate_sharpe_ratio(self, trades: List[Trade], capital: float, risk_free_rate: float = 0.02) -> float:
        """
        Calculate Sharpe ratio - risk-adjusted return
        """
        if len(trades) < 2 or capital == 0:
            return 0

        returns = [(trade.pnl / capital) * 100 for trade in trades]
        avg_return = np.mean(returns)
        std_return = np.std(returns)

        if std_return == 0:
            return 0

        # Annualized Sharpe
        sharpe = (avg_return - risk_free_rate / 365) / std_return * np.sqrt(365)

        return sharpe

    def _calculate_sortino_ratio(self, trades: List[Trade], capital: float, risk_free_rate: float = 0.02) -> float:
        """
        Calculate Sortino ratio - like Sharpe but only considers downside volatility
        """
        if len(trades) < 2 or capital == 0:
            return 0

        returns = [(trade.pnl / capital) * 100 for trade in trades]
        avg_return = np.mean(returns)

        # Downside deviation (only negative returns)
        downside_returns = [r for r in returns if r < 0]
        if not downside_returns:
            return 0

        downside_std = np.std(downside_returns)
        if downside_std == 0:
            return 0

        # Annualized Sortino
        sortino = (avg_return - risk_free_rate / 365) / downside_std * np.sqrt(365)

        return sortino

    def _calculate_max_drawdown(self, trades: List[Trade], initial_capital: float) -> float:
        """
        Calculate maximum drawdown from peak equity
        """
        if not trades:
            return 0

        # Sort trades by close time
        sorted_trades = sorted(trades, key=lambda t: t.closed_at if t.closed_at else datetime.utcnow())

        equity = initial_capital
        peak = equity
        max_dd = 0

        for trade in sorted_trades:
            equity += trade.pnl
            if equity > peak:
                peak = equity
            dd = peak - equity
            if dd > max_dd:
                max_dd = dd

        return max_dd

    def _calculate_current_drawdown(self, bots: List[Bot]) -> float:
        """
        Calculate current drawdown from peak portfolio value
        """
        current_value = sum(bot.current_balance for bot in bots)
        initial_capital = sum(bot.capital for bot in bots)

        # Simple drawdown calculation
        if current_value < initial_capital:
            return initial_capital - current_value

        return 0

    def _calculate_risk_score(self, var: float, volatility: float, max_dd: float,
                            current_dd: float, portfolio_value: float) -> float:
        """
        Calculate overall risk score (0-100, lower is better)
        """
        if portfolio_value == 0:
            return 100

        # Normalize metrics to 0-100 scale
        var_score = min((var / portfolio_value) * 100 * 10, 30)  # Max 30 points
        vol_score = min((volatility / portfolio_value) * 100 * 5, 25)  # Max 25 points
        dd_score = min((max_dd / portfolio_value) * 100 * 2, 30)  # Max 30 points
        current_dd_score = min((current_dd / portfolio_value) * 100 * 10, 15)  # Max 15 points

        total_score = var_score + vol_score + dd_score + current_dd_score

        return min(total_score, 100)

    def _get_risk_level(self, risk_score: float) -> str:
        """
        Get risk level description from score
        """
        if risk_score < 20:
            return 'Very Low'
        elif risk_score < 40:
            return 'Low'
        elif risk_score < 60:
            return 'Moderate'
        elif risk_score < 80:
            return 'High'
        else:
            return 'Very High'

    def _calculate_exposure(self, bots: List[Bot]) -> Dict:
        """
        Calculate position exposure across exchanges and symbols
        """
        exposure = {
            'total': 0,
            'by_exchange': {},
            'by_symbol': {}
        }

        # Get open trades
        for bot in bots:
            open_trades = self.db.query(Trade).filter(
                Trade.bot_id == bot.id,
                Trade.status == 'open'
            ).all()

            for trade in open_trades:
                position_value = trade.quantity * trade.entry_price
                exposure['total'] += position_value

                # By exchange
                exchange = bot.exchange
                exposure['by_exchange'][exchange] = exposure['by_exchange'].get(exchange, 0) + position_value

                # By symbol
                symbol = trade.symbol
                exposure['by_symbol'][symbol] = exposure['by_symbol'].get(symbol, 0) + position_value

        return exposure

    def _empty_risk_metrics(self) -> Dict:
        """Return empty risk metrics structure"""
        return {
            'total_value': 0,
            'total_invested': 0,
            'total_pnl': 0,
            'value_at_risk_95': 0,
            'value_at_risk_99': 0,
            'conditional_var_95': 0,
            'volatility': 0,
            'sharpe_ratio': 0,
            'sortino_ratio': 0,
            'max_drawdown': 0,
            'max_drawdown_percent': 0,
            'current_drawdown': 0,
            'current_drawdown_percent': 0,
            'risk_score': 0,
            'risk_level': 'Unknown',
            'total_exposure': 0,
            'exposure_by_exchange': {},
            'exposure_by_symbol': {},
            'total_trades': 0,
            'active_bots': 0
        }

    def check_risk_limits(self, trade_params: Dict) -> Tuple[bool, str]:
        """
        Check if a proposed trade violates risk limits

        Args:
            trade_params: Dict with trade details (symbol, size, etc.)

        Returns:
            (allowed: bool, reason: str)
        """
        try:
            risk_metrics = self.calculate_portfolio_risk()

            # Check max drawdown limit
            if risk_metrics['current_drawdown_percent'] > 20:
                return False, "Portfolio drawdown exceeds 20% limit"

            # Check risk score
            if risk_metrics['risk_score'] > 85:
                return False, "Portfolio risk score too high"

            # Check exposure limits
            if risk_metrics['total_exposure'] > risk_metrics['total_value'] * 5:
                return False, "Total exposure exceeds 5x portfolio value"

            return True, "Trade allowed"

        except Exception as e:
            logger.error(f"❌ Risk limit check failed: {str(e)}")
            return True, "Risk check bypassed due to error"

    def get_position_size_recommendation(self, symbol: str, entry_price: float,
                                        stop_loss: float) -> Dict:
        """
        Calculate recommended position size based on portfolio risk

        Args:
            symbol: Trading symbol
            entry_price: Planned entry price
            stop_loss: Stop loss price

        Returns:
            Position sizing recommendation
        """
        try:
            risk_metrics = self.calculate_portfolio_risk()
            portfolio_value = risk_metrics['total_value']

            if portfolio_value == 0:
                return {'recommended_size': 0, 'risk_percent': 0, 'reason': 'No portfolio value'}

            # Risk per trade: 1-2% of portfolio based on risk score
            if risk_metrics['risk_score'] < 30:
                risk_per_trade = 0.02  # 2% for low risk
            elif risk_metrics['risk_score'] < 60:
                risk_per_trade = 0.015  # 1.5% for moderate risk
            else:
                risk_per_trade = 0.01  # 1% for high risk

            # Calculate position size
            risk_amount = portfolio_value * risk_per_trade
            price_risk = abs(entry_price - stop_loss)

            if price_risk == 0:
                return {'recommended_size': 0, 'risk_percent': 0, 'reason': 'Invalid stop loss'}

            recommended_quantity = risk_amount / price_risk
            position_value = recommended_quantity * entry_price

            return {
                'recommended_quantity': round(recommended_quantity, 8),
                'position_value': round(position_value, 2),
                'risk_amount': round(risk_amount, 2),
                'risk_percent': round(risk_per_trade * 100, 2),
                'portfolio_value': round(portfolio_value, 2),
                'reason': f"Based on {risk_metrics['risk_level']} risk level"
            }

        except Exception as e:
            logger.error(f"❌ Position sizing failed: {str(e)}")
            return {'recommended_size': 0, 'risk_percent': 0, 'reason': str(e)}


def calculate_correlation_matrix(db: Session, user_id: int) -> Dict:
    """
    Calculate correlation matrix between different trading symbols

    Returns:
        Correlation data for portfolio diversification analysis
    """
    try:
        # Get user's bots
        bots = db.query(Bot).filter(Bot.user_id == user_id).all()

        # Collect trades by symbol
        symbol_returns = {}

        for bot in bots:
            trades = db.query(Trade).filter(
                Trade.bot_id == bot.id,
                Trade.status == 'closed',
                Trade.pnl.isnot(None)
            ).all()

            for trade in trades:
                if trade.symbol not in symbol_returns:
                    symbol_returns[trade.symbol] = []

                # Calculate return percentage
                return_pct = (trade.pnl / (trade.quantity * trade.entry_price)) * 100 if trade.entry_price > 0 else 0
                symbol_returns[trade.symbol].append(return_pct)

        if len(symbol_returns) < 2:
            return {'correlation_matrix': {}, 'message': 'Need at least 2 symbols for correlation'}

        # Calculate pairwise correlations
        correlation_matrix = {}
        symbols = list(symbol_returns.keys())

        for i, sym1 in enumerate(symbols):
            correlation_matrix[sym1] = {}
            for sym2 in symbols:
                if len(symbol_returns[sym1]) < 2 or len(symbol_returns[sym2]) < 2:
                    correlation_matrix[sym1][sym2] = 0
                    continue

                # Ensure equal length arrays
                min_len = min(len(symbol_returns[sym1]), len(symbol_returns[sym2]))
                returns1 = symbol_returns[sym1][:min_len]
                returns2 = symbol_returns[sym2][:min_len]

                # Calculate correlation
                correlation = np.corrcoef(returns1, returns2)[0, 1]
                correlation_matrix[sym1][sym2] = round(float(correlation), 3)

        return {
            'correlation_matrix': correlation_matrix,
            'symbols': symbols,
            'diversification_score': calculate_diversification_score(correlation_matrix)
        }

    except Exception as e:
        logger.error(f"❌ Correlation calculation failed: {str(e)}")
        return {'correlation_matrix': {}, 'error': str(e)}


def calculate_diversification_score(correlation_matrix: Dict) -> float:
    """
    Calculate portfolio diversification score (0-100, higher is better)
    """
    if not correlation_matrix:
        return 0

    # Average absolute correlation (excluding diagonal)
    correlations = []
    for sym1, corr_data in correlation_matrix.items():
        for sym2, corr_value in corr_data.items():
            if sym1 != sym2 and not np.isnan(corr_value):
                correlations.append(abs(corr_value))

    if not correlations:
        return 0

    avg_correlation = np.mean(correlations)

    # Convert to 0-100 score (lower correlation = higher score)
    diversification_score = (1 - avg_correlation) * 100

    return round(diversification_score, 1)
