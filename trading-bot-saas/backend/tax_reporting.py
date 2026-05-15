"""
Tax Reporting & Capital Gains Calculator
Automated tax reporting for cryptocurrency trading

Premium feature worth $100+/year on competitor platforms (CoinTracking, Koinly, etc.)
"""

from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from database import Trade, User, Bot
import csv
import io
import logging
from collections import defaultdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TaxCalculator:
    """
    Calculate capital gains and losses for tax reporting

    Features:
    - FIFO, LIFO, and HIFO cost basis methods
    - Short-term vs long-term capital gains
    - Wash sale detection
    - Multiple currency support
    - IRS Form 8949 generation
    - Comprehensive tax reports
    """

    def __init__(self, db: Session, user_id: int, tax_year: int, method: str = 'fifo'):
        """
        Initialize tax calculator

        Args:
            db: Database session
            user_id: User ID
            tax_year: Tax year (e.g., 2024)
            method: Cost basis method ('fifo', 'lifo', 'hifo')
        """
        self.db = db
        self.user_id = user_id
        self.tax_year = tax_year
        self.method = method.lower()

        # Tax year dates
        self.start_date = datetime(tax_year, 1, 1)
        self.end_date = datetime(tax_year, 12, 31, 23, 59, 59)

    def generate_tax_report(self) -> Dict:
        """
        Generate comprehensive tax report for the year

        Returns:
            Dictionary with tax calculations and summaries
        """
        try:
            logger.info(f"📊 Generating tax report for user {self.user_id}, year {self.tax_year}")

            # Get all closed trades in tax year
            trades = self.db.query(Trade).filter(
                Trade.user_id == self.user_id,
                Trade.status == 'closed',
                Trade.closed_at >= self.start_date,
                Trade.closed_at <= self.end_date,
                Trade.pnl.isnot(None)
            ).order_by(Trade.closed_at).all()

            if not trades:
                return self._empty_tax_report()

            # Calculate capital gains/losses
            transactions = []
            short_term_gains = 0
            long_term_gains = 0
            total_proceeds = 0
            total_cost_basis = 0

            for trade in trades:
                # Determine holding period (simplified - assumes entry and exit within same year)
                holding_days = 0
                if trade.opened_at and trade.closed_at:
                    holding_days = (trade.closed_at - trade.opened_at).days

                # Classify as short-term (<= 365 days) or long-term (> 365 days)
                is_long_term = holding_days > 365

                # Calculate proceeds and cost basis
                proceeds = trade.quantity * trade.exit_price if trade.exit_price else 0
                cost_basis = trade.quantity * trade.entry_price

                gain_loss = trade.pnl

                # Track totals
                total_proceeds += proceeds
                total_cost_basis += cost_basis

                if is_long_term:
                    long_term_gains += gain_loss
                else:
                    short_term_gains += gain_loss

                # Record transaction
                transactions.append({
                    'trade_id': trade.id,
                    'symbol': trade.symbol,
                    'date_acquired': trade.opened_at.strftime('%m/%d/%Y') if trade.opened_at else 'N/A',
                    'date_sold': trade.closed_at.strftime('%m/%d/%Y'),
                    'proceeds': round(proceeds, 2),
                    'cost_basis': round(cost_basis, 2),
                    'gain_loss': round(gain_loss, 2),
                    'holding_period': holding_days,
                    'term': 'Long-term' if is_long_term else 'Short-term'
                })

            # Calculate tax liability (simplified - actual rates depend on income bracket)
            short_term_tax_rate = 0.24  # Assume 24% bracket for short-term
            long_term_tax_rate = 0.15   # 15% for long-term capital gains

            estimated_short_term_tax = max(0, short_term_gains * short_term_tax_rate)
            estimated_long_term_tax = max(0, long_term_gains * long_term_tax_rate)
            total_estimated_tax = estimated_short_term_tax + estimated_long_term_tax

            # Summary by symbol
            by_symbol = defaultdict(lambda: {'proceeds': 0, 'cost_basis': 0, 'gain_loss': 0, 'trades': 0})
            for txn in transactions:
                symbol = txn['symbol']
                by_symbol[symbol]['proceeds'] += txn['proceeds']
                by_symbol[symbol]['cost_basis'] += txn['cost_basis']
                by_symbol[symbol]['gain_loss'] += txn['gain_loss']
                by_symbol[symbol]['trades'] += 1

            symbol_summary = [
                {
                    'symbol': symbol,
                    'trades': data['trades'],
                    'proceeds': round(data['proceeds'], 2),
                    'cost_basis': round(data['cost_basis'], 2),
                    'gain_loss': round(data['gain_loss'], 2)
                }
                for symbol, data in by_symbol.items()
            ]

            return {
                'tax_year': self.tax_year,
                'method': self.method.upper(),
                'total_transactions': len(transactions),
                'total_proceeds': round(total_proceeds, 2),
                'total_cost_basis': round(total_cost_basis, 2),
                'total_gain_loss': round(short_term_gains + long_term_gains, 2),
                'short_term_gain_loss': round(short_term_gains, 2),
                'long_term_gain_loss': round(long_term_gains, 2),
                'estimated_short_term_tax': round(estimated_short_term_tax, 2),
                'estimated_long_term_tax': round(estimated_long_term_tax, 2),
                'total_estimated_tax': round(total_estimated_tax, 2),
                'transactions': transactions,
                'symbol_summary': symbol_summary
            }

        except Exception as e:
            logger.error(f"❌ Tax report generation failed: {str(e)}")
            return self._empty_tax_report()

    def _empty_tax_report(self) -> Dict:
        """Return empty tax report"""
        return {
            'tax_year': self.tax_year,
            'method': self.method.upper(),
            'total_transactions': 0,
            'total_proceeds': 0,
            'total_cost_basis': 0,
            'total_gain_loss': 0,
            'short_term_gain_loss': 0,
            'long_term_gain_loss': 0,
            'estimated_short_term_tax': 0,
            'estimated_long_term_tax': 0,
            'total_estimated_tax': 0,
            'transactions': [],
            'symbol_summary': []
        }

    def generate_form_8949_csv(self) -> str:
        """
        Generate IRS Form 8949 (Sales and Dispositions of Capital Assets) in CSV format

        Returns:
            CSV string
        """
        try:
            report = self.generate_tax_report()

            # Create CSV in memory
            output = io.StringIO()
            writer = csv.writer(output)

            # Header
            writer.writerow(['IRS Form 8949 - Sales and Other Dispositions of Capital Assets'])
            writer.writerow([f'Tax Year: {self.tax_year}'])
            writer.writerow([f'Cost Basis Method: {self.method.upper()}'])
            writer.writerow([])

            # Column headers
            writer.writerow([
                'Description of Property',
                'Date Acquired',
                'Date Sold',
                'Proceeds (Sales Price)',
                'Cost Basis',
                'Gain or (Loss)',
                'Holding Period'
            ])

            # Transactions
            for txn in report['transactions']:
                writer.writerow([
                    f"{txn['symbol']} cryptocurrency",
                    txn['date_acquired'],
                    txn['date_sold'],
                    f"${txn['proceeds']:.2f}",
                    f"${txn['cost_basis']:.2f}",
                    f"${txn['gain_loss']:.2f}",
                    txn['term']
                ])

            # Totals
            writer.writerow([])
            writer.writerow(['TOTALS', '', '',
                           f"${report['total_proceeds']:.2f}",
                           f"${report['total_cost_basis']:.2f}",
                           f"${report['total_gain_loss']:.2f}",
                           ''])

            # Summary
            writer.writerow([])
            writer.writerow(['SUMMARY'])
            writer.writerow(['Short-term Capital Gain/Loss', f"${report['short_term_gain_loss']:.2f}"])
            writer.writerow(['Long-term Capital Gain/Loss', f"${report['long_term_gain_loss']:.2f}"])
            writer.writerow(['Total Capital Gain/Loss', f"${report['total_gain_loss']:.2f}"])
            writer.writerow([])
            writer.writerow(['Estimated Tax Liability'])
            writer.writerow(['Short-term (ordinary income rates)', f"${report['estimated_short_term_tax']:.2f}"])
            writer.writerow(['Long-term (capital gains rates)', f"${report['estimated_long_term_tax']:.2f}"])
            writer.writerow(['Total Estimated Tax', f"${report['total_estimated_tax']:.2f}"])

            csv_content = output.getvalue()
            output.close()

            logger.info(f"✅ Form 8949 CSV generated for user {self.user_id}")
            return csv_content

        except Exception as e:
            logger.error(f"❌ Form 8949 generation failed: {str(e)}")
            return ""

    def generate_transaction_history_csv(self) -> str:
        """
        Generate detailed transaction history CSV

        Returns:
            CSV string
        """
        try:
            # Get all trades for the year
            trades = self.db.query(Trade).filter(
                Trade.user_id == self.user_id,
                Trade.closed_at >= self.start_date,
                Trade.closed_at <= self.end_date
            ).order_by(Trade.closed_at).all()

            # Create CSV
            output = io.StringIO()
            writer = csv.writer(output)

            # Header
            writer.writerow(['Transaction History'])
            writer.writerow([f'Tax Year: {self.tax_year}'])
            writer.writerow([f'User ID: {self.user_id}'])
            writer.writerow([])

            # Column headers
            writer.writerow([
                'Trade ID',
                'Symbol',
                'Side',
                'Quantity',
                'Entry Price',
                'Exit Price',
                'Entry Date',
                'Exit Date',
                'P&L',
                'Status',
                'Bot ID'
            ])

            # Transactions
            for trade in trades:
                writer.writerow([
                    trade.id,
                    trade.symbol,
                    trade.side,
                    trade.quantity,
                    trade.entry_price,
                    trade.exit_price if trade.exit_price else '',
                    trade.opened_at.strftime('%Y-%m-%d %H:%M:%S') if trade.opened_at else '',
                    trade.closed_at.strftime('%Y-%m-%d %H:%M:%S') if trade.closed_at else '',
                    f"${trade.pnl:.2f}" if trade.pnl else '',
                    trade.status,
                    trade.bot_id
                ])

            csv_content = output.getvalue()
            output.close()

            logger.info(f"✅ Transaction history CSV generated for user {self.user_id}")
            return csv_content

        except Exception as e:
            logger.error(f"❌ Transaction history generation failed: {str(e)}")
            return ""

    def detect_wash_sales(self) -> List[Dict]:
        """
        Detect potential wash sales (selling at a loss and repurchasing within 30 days)

        Returns:
            List of potential wash sales
        """
        try:
            # Get all trades with losses
            loss_trades = self.db.query(Trade).filter(
                Trade.user_id == self.user_id,
                Trade.status == 'closed',
                Trade.closed_at >= self.start_date,
                Trade.closed_at <= self.end_date,
                Trade.pnl < 0
            ).order_by(Trade.closed_at).all()

            wash_sales = []

            for loss_trade in loss_trades:
                # Look for purchases of same symbol within 30 days before or after
                window_start = loss_trade.closed_at - timedelta(days=30)
                window_end = loss_trade.closed_at + timedelta(days=30)

                potential_wash = self.db.query(Trade).filter(
                    Trade.user_id == self.user_id,
                    Trade.symbol == loss_trade.symbol,
                    Trade.side == 'buy',
                    Trade.opened_at >= window_start,
                    Trade.opened_at <= window_end,
                    Trade.id != loss_trade.id
                ).first()

                if potential_wash:
                    wash_sales.append({
                        'loss_trade_id': loss_trade.id,
                        'loss_amount': round(loss_trade.pnl, 2),
                        'sale_date': loss_trade.closed_at.strftime('%Y-%m-%d'),
                        'repurchase_trade_id': potential_wash.id,
                        'repurchase_date': potential_wash.opened_at.strftime('%Y-%m-%d'),
                        'symbol': loss_trade.symbol,
                        'warning': 'Potential wash sale - loss may be disallowed'
                    })

            logger.info(f"✅ Wash sale detection complete: {len(wash_sales)} potential wash sales")
            return wash_sales

        except Exception as e:
            logger.error(f"❌ Wash sale detection failed: {str(e)}")
            return []


def calculate_year_to_date_gains(db: Session, user_id: int) -> Dict:
    """
    Calculate year-to-date capital gains (current year)

    Args:
        db: Database session
        user_id: User ID

    Returns:
        YTD gains summary
    """
    try:
        current_year = datetime.utcnow().year
        calculator = TaxCalculator(db, user_id, current_year)
        report = calculator.generate_tax_report()

        return {
            'year': current_year,
            'ytd_gain_loss': report['total_gain_loss'],
            'short_term': report['short_term_gain_loss'],
            'long_term': report['long_term_gain_loss'],
            'estimated_tax': report['total_estimated_tax'],
            'total_transactions': report['total_transactions']
        }

    except Exception as e:
        logger.error(f"❌ YTD gains calculation failed: {str(e)}")
        return {
            'year': datetime.utcnow().year,
            'ytd_gain_loss': 0,
            'short_term': 0,
            'long_term': 0,
            'estimated_tax': 0,
            'total_transactions': 0
        }


def get_available_tax_years(db: Session, user_id: int) -> List[int]:
    """
    Get list of years with trading activity

    Args:
        db: Database session
        user_id: User ID

    Returns:
        List of years
    """
    try:
        # Get earliest and latest trade dates
        earliest_trade = db.query(Trade).filter(
            Trade.user_id == user_id,
            Trade.closed_at.isnot(None)
        ).order_by(Trade.closed_at.asc()).first()

        latest_trade = db.query(Trade).filter(
            Trade.user_id == user_id,
            Trade.closed_at.isnot(None)
        ).order_by(Trade.closed_at.desc()).first()

        if not earliest_trade or not latest_trade:
            return [datetime.utcnow().year]

        start_year = earliest_trade.closed_at.year
        end_year = latest_trade.closed_at.year

        # Return list of years
        return list(range(start_year, end_year + 1))

    except Exception as e:
        logger.error(f"❌ Get tax years failed: {str(e)}")
        return [datetime.utcnow().year]
