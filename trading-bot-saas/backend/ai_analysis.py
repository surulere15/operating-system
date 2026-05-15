"""
AI Market Analysis Module
Provides AI-powered market insights, predictions, and trading signals

Premium feature worth $50-100/month on competitor platforms
"""

from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from database import Trade, User, Bot
import logging
from collections import defaultdict
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AIAnalyzer:
    """
    AI-powered market analysis and trading insights

    Features:
    - Market sentiment analysis
    - Price prediction insights
    - Technical analysis recommendations
    - Pattern recognition
    - Risk assessments
    - Trading signal generation
    """

    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id

    def analyze_market_sentiment(self, symbol: str) -> Dict:
        """
        Analyze market sentiment for a given symbol

        Args:
            symbol: Trading symbol (e.g., 'BTC/USDT')

        Returns:
            Sentiment analysis with score and indicators
        """
        try:
            # Get recent trades for the symbol
            recent_trades = self.db.query(Trade).filter(
                Trade.user_id == self.user_id,
                Trade.symbol == symbol,
                Trade.closed_at >= datetime.utcnow() - timedelta(days=30)
            ).order_by(Trade.closed_at.desc()).limit(100).all()

            if not recent_trades:
                return self._empty_sentiment()

            # Calculate sentiment indicators
            winning_trades = len([t for t in recent_trades if t.pnl and t.pnl > 0])
            total_trades = len(recent_trades)
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

            avg_pnl = sum([t.pnl for t in recent_trades if t.pnl]) / total_trades if total_trades > 0 else 0

            # Calculate price momentum (based on recent trades)
            price_changes = []
            for i in range(len(recent_trades) - 1):
                if recent_trades[i].exit_price and recent_trades[i+1].entry_price:
                    change = ((recent_trades[i].exit_price - recent_trades[i+1].entry_price) /
                             recent_trades[i+1].entry_price * 100)
                    price_changes.append(change)

            momentum = sum(price_changes) / len(price_changes) if price_changes else 0

            # Calculate sentiment score (0-100)
            sentiment_score = self._calculate_sentiment_score(win_rate, avg_pnl, momentum)

            # Generate sentiment label
            if sentiment_score >= 70:
                sentiment_label = "Very Bullish"
                sentiment_emoji = "🚀"
            elif sentiment_score >= 60:
                sentiment_label = "Bullish"
                sentiment_emoji = "📈"
            elif sentiment_score >= 40:
                sentiment_label = "Neutral"
                sentiment_emoji = "➡️"
            elif sentiment_score >= 30:
                sentiment_label = "Bearish"
                sentiment_emoji = "📉"
            else:
                sentiment_label = "Very Bearish"
                sentiment_emoji = "⚠️"

            return {
                'symbol': symbol,
                'sentiment_score': round(sentiment_score, 2),
                'sentiment_label': sentiment_label,
                'sentiment_emoji': sentiment_emoji,
                'win_rate': round(win_rate, 2),
                'avg_pnl': round(avg_pnl, 2),
                'momentum': round(momentum, 2),
                'total_trades_analyzed': total_trades,
                'timestamp': datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"❌ Sentiment analysis failed: {str(e)}")
            return self._empty_sentiment()

    def generate_trading_signals(self, symbol: str) -> List[Dict]:
        """
        Generate AI trading signals based on market analysis

        Args:
            symbol: Trading symbol

        Returns:
            List of trading signals with confidence scores
        """
        try:
            # Get recent trading data
            recent_trades = self.db.query(Trade).filter(
                Trade.user_id == self.user_id,
                Trade.symbol == symbol,
                Trade.closed_at >= datetime.utcnow() - timedelta(days=14)
            ).order_by(Trade.closed_at.desc()).all()

            signals = []

            if len(recent_trades) < 10:
                return [{
                    'signal': 'INSUFFICIENT_DATA',
                    'action': 'gather_more_data',
                    'confidence': 0,
                    'reason': 'Need at least 10 recent trades for reliable signals'
                }]

            # Analyze various indicators

            # 1. Trend analysis
            trend_signal = self._analyze_trend(recent_trades)
            if trend_signal:
                signals.append(trend_signal)

            # 2. Volatility analysis
            volatility_signal = self._analyze_volatility(recent_trades)
            if volatility_signal:
                signals.append(volatility_signal)

            # 3. Support/Resistance levels
            sr_signal = self._analyze_support_resistance(recent_trades)
            if sr_signal:
                signals.append(sr_signal)

            # 4. Momentum indicators
            momentum_signal = self._analyze_momentum(recent_trades)
            if momentum_signal:
                signals.append(momentum_signal)

            # 5. Risk assessment
            risk_signal = self._analyze_risk(recent_trades)
            if risk_signal:
                signals.append(risk_signal)

            return signals

        except Exception as e:
            logger.error(f"❌ Signal generation failed: {str(e)}")
            return []

    def get_ai_insights(self, symbol: Optional[str] = None) -> Dict:
        """
        Get comprehensive AI insights for portfolio or specific symbol

        Args:
            symbol: Optional symbol to analyze (if None, analyzes entire portfolio)

        Returns:
            Comprehensive AI insights
        """
        try:
            if symbol:
                # Analyze specific symbol
                sentiment = self.analyze_market_sentiment(symbol)
                signals = self.generate_trading_signals(symbol)

                return {
                    'symbol': symbol,
                    'sentiment': sentiment,
                    'signals': signals,
                    'recommendations': self._generate_recommendations(sentiment, signals),
                    'timestamp': datetime.utcnow().isoformat()
                }
            else:
                # Analyze entire portfolio
                all_trades = self.db.query(Trade).filter(
                    Trade.user_id == self.user_id,
                    Trade.closed_at >= datetime.utcnow() - timedelta(days=30)
                ).all()

                # Get unique symbols
                symbols = list(set([t.symbol for t in all_trades]))

                # Analyze each symbol
                symbol_insights = []
                for sym in symbols[:5]:  # Limit to top 5 symbols
                    insight = self.get_ai_insights(sym)
                    symbol_insights.append(insight)

                # Portfolio-level insights
                total_pnl = sum([t.pnl for t in all_trades if t.pnl])
                win_rate = (len([t for t in all_trades if t.pnl and t.pnl > 0]) /
                           len(all_trades) * 100) if all_trades else 0

                return {
                    'portfolio_summary': {
                        'total_pnl': round(total_pnl, 2),
                        'win_rate': round(win_rate, 2),
                        'symbols_tracked': len(symbols),
                        'total_trades': len(all_trades)
                    },
                    'symbol_insights': symbol_insights,
                    'overall_recommendation': self._generate_portfolio_recommendation(symbol_insights),
                    'timestamp': datetime.utcnow().isoformat()
                }

        except Exception as e:
            logger.error(f"❌ AI insights generation failed: {str(e)}")
            return {}

    def predict_price_movement(self, symbol: str, timeframe: str = '24h') -> Dict:
        """
        Predict price movement for the next timeframe

        Args:
            symbol: Trading symbol
            timeframe: Prediction timeframe ('1h', '4h', '24h', '7d')

        Returns:
            Price prediction with confidence interval
        """
        try:
            # Get historical data
            lookback_days = {'1h': 3, '4h': 7, '24h': 14, '7d': 30}
            days = lookback_days.get(timeframe, 14)

            recent_trades = self.db.query(Trade).filter(
                Trade.user_id == self.user_id,
                Trade.symbol == symbol,
                Trade.closed_at >= datetime.utcnow() - timedelta(days=days)
            ).order_by(Trade.closed_at.desc()).all()

            if len(recent_trades) < 5:
                return {
                    'prediction': 'insufficient_data',
                    'confidence': 0,
                    'message': 'Need more historical data for predictions'
                }

            # Calculate average price movement
            price_changes = []
            for trade in recent_trades:
                if trade.entry_price and trade.exit_price:
                    change_pct = ((trade.exit_price - trade.entry_price) / trade.entry_price * 100)
                    price_changes.append(change_pct)

            if not price_changes:
                return {
                    'prediction': 'no_data',
                    'confidence': 0
                }

            avg_change = sum(price_changes) / len(price_changes)
            volatility = self._calculate_std_dev(price_changes)

            # Get current price (from most recent trade)
            current_price = recent_trades[0].exit_price if recent_trades[0].exit_price else recent_trades[0].entry_price

            # Predict price range
            predicted_change = avg_change * 1.2  # Slight adjustment factor
            predicted_price = current_price * (1 + predicted_change / 100)

            lower_bound = predicted_price * (1 - volatility / 100)
            upper_bound = predicted_price * (1 + volatility / 100)

            # Calculate confidence (0-100)
            confidence = max(0, min(100, 100 - (volatility * 5)))

            # Direction
            direction = 'up' if predicted_change > 0.5 else 'down' if predicted_change < -0.5 else 'sideways'

            return {
                'symbol': symbol,
                'timeframe': timeframe,
                'current_price': round(current_price, 2),
                'predicted_price': round(predicted_price, 2),
                'predicted_change_percent': round(predicted_change, 2),
                'direction': direction,
                'confidence': round(confidence, 2),
                'price_range': {
                    'lower': round(lower_bound, 2),
                    'upper': round(upper_bound, 2)
                },
                'volatility': round(volatility, 2),
                'timestamp': datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"❌ Price prediction failed: {str(e)}")
            return {}

    # Helper methods

    def _calculate_sentiment_score(self, win_rate: float, avg_pnl: float, momentum: float) -> float:
        """Calculate sentiment score from indicators"""
        # Weighted average
        score = (
            (win_rate * 0.4) +  # 40% weight on win rate
            (min(100, max(0, 50 + avg_pnl * 10)) * 0.3) +  # 30% weight on avg PnL
            (min(100, max(0, 50 + momentum * 5)) * 0.3)    # 30% weight on momentum
        )
        return max(0, min(100, score))

    def _analyze_trend(self, trades: List[Trade]) -> Optional[Dict]:
        """Analyze trend direction"""
        if len(trades) < 5:
            return None

        prices = [t.exit_price for t in trades if t.exit_price]
        if len(prices) < 5:
            return None

        # Simple trend detection
        recent_avg = sum(prices[:len(prices)//2]) / (len(prices)//2)
        older_avg = sum(prices[len(prices)//2:]) / (len(prices) - len(prices)//2)

        trend_strength = abs(recent_avg - older_avg) / older_avg * 100

        if recent_avg > older_avg * 1.02:
            return {
                'signal': 'UPTREND',
                'action': 'consider_long',
                'confidence': min(100, trend_strength * 10),
                'reason': f'Price showing upward trend with {trend_strength:.1f}% momentum'
            }
        elif recent_avg < older_avg * 0.98:
            return {
                'signal': 'DOWNTREND',
                'action': 'consider_short',
                'confidence': min(100, trend_strength * 10),
                'reason': f'Price showing downward trend with {trend_strength:.1f}% momentum'
            }
        return None

    def _analyze_volatility(self, trades: List[Trade]) -> Optional[Dict]:
        """Analyze market volatility"""
        price_changes = []
        for i in range(len(trades) - 1):
            if trades[i].exit_price and trades[i+1].exit_price:
                change = abs((trades[i].exit_price - trades[i+1].exit_price) / trades[i+1].exit_price * 100)
                price_changes.append(change)

        if not price_changes:
            return None

        volatility = sum(price_changes) / len(price_changes)

        if volatility > 5:
            return {
                'signal': 'HIGH_VOLATILITY',
                'action': 'reduce_position_size',
                'confidence': 80,
                'reason': f'High volatility detected ({volatility:.1f}%). Consider reducing position sizes.'
            }
        elif volatility < 1:
            return {
                'signal': 'LOW_VOLATILITY',
                'action': 'increase_position_size',
                'confidence': 70,
                'reason': f'Low volatility environment ({volatility:.1f}%). Conditions favorable for larger positions.'
            }
        return None

    def _analyze_support_resistance(self, trades: List[Trade]) -> Optional[Dict]:
        """Identify support/resistance levels"""
        prices = [t.exit_price for t in trades if t.exit_price]
        if len(prices) < 10:
            return None

        # Find price levels that appear multiple times (simplified)
        price_clusters = defaultdict(int)
        for price in prices:
            # Round to nearest significant level
            level = round(price / 100) * 100
            price_clusters[level] += 1

        # Find most common level
        if price_clusters:
            key_level = max(price_clusters, key=price_clusters.get)
            current_price = prices[0]

            if current_price < key_level * 0.98:
                return {
                    'signal': 'APPROACHING_RESISTANCE',
                    'action': 'watch_for_breakout',
                    'confidence': 65,
                    'reason': f'Price approaching resistance at ${key_level:.2f}'
                }
            elif current_price > key_level * 1.02:
                return {
                    'signal': 'ABOVE_SUPPORT',
                    'action': 'watch_for_bounce',
                    'confidence': 65,
                    'reason': f'Price holding above support at ${key_level:.2f}'
                }

        return None

    def _analyze_momentum(self, trades: List[Trade]) -> Optional[Dict]:
        """Analyze momentum indicators"""
        if len(trades) < 5:
            return None

        recent_pnls = [t.pnl for t in trades[:5] if t.pnl]
        if len(recent_pnls) < 3:
            return None

        momentum_score = sum(recent_pnls) / len(recent_pnls)

        if momentum_score > 10:
            return {
                'signal': 'STRONG_MOMENTUM',
                'action': 'ride_the_trend',
                'confidence': 75,
                'reason': 'Strong positive momentum in recent trades'
            }
        elif momentum_score < -10:
            return {
                'signal': 'NEGATIVE_MOMENTUM',
                'action': 'reduce_exposure',
                'confidence': 75,
                'reason': 'Negative momentum detected, consider reducing exposure'
            }

        return None

    def _analyze_risk(self, trades: List[Trade]) -> Optional[Dict]:
        """Assess current risk level"""
        losing_streak = 0
        for trade in trades:
            if trade.pnl and trade.pnl < 0:
                losing_streak += 1
            else:
                break

        if losing_streak >= 3:
            return {
                'signal': 'HIGH_RISK',
                'action': 'pause_trading',
                'confidence': 90,
                'reason': f'Losing streak detected ({losing_streak} trades). Consider pausing to reassess strategy.'
            }

        return None

    def _generate_recommendations(self, sentiment: Dict, signals: List[Dict]) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []

        # Based on sentiment
        if sentiment.get('sentiment_score', 0) > 70:
            recommendations.append("Strong bullish sentiment - Consider increasing position sizes")
        elif sentiment.get('sentiment_score', 0) < 30:
            recommendations.append("Bearish sentiment detected - Exercise caution or consider short positions")

        # Based on signals
        high_confidence_signals = [s for s in signals if s.get('confidence', 0) > 70]
        if high_confidence_signals:
            for signal in high_confidence_signals[:3]:  # Top 3 high-confidence signals
                recommendations.append(f"{signal['signal']}: {signal['reason']}")

        if not recommendations:
            recommendations.append("Neutral market conditions - Wait for clearer signals")

        return recommendations

    def _generate_portfolio_recommendation(self, symbol_insights: List[Dict]) -> str:
        """Generate overall portfolio recommendation"""
        if not symbol_insights:
            return "Insufficient data for portfolio recommendation"

        # Count bullish vs bearish symbols
        bullish_count = sum(1 for insight in symbol_insights
                          if insight.get('sentiment', {}).get('sentiment_score', 50) > 60)
        bearish_count = sum(1 for insight in symbol_insights
                          if insight.get('sentiment', {}).get('sentiment_score', 50) < 40)

        if bullish_count > bearish_count * 2:
            return "Portfolio showing strong bullish signals across multiple assets. Consider maintaining or increasing exposure."
        elif bearish_count > bullish_count * 2:
            return "Portfolio showing bearish signals. Consider defensive positioning or reducing exposure."
        else:
            return "Mixed signals across portfolio. Maintain balanced approach and monitor key levels."

    def _calculate_std_dev(self, values: List[float]) -> float:
        """Calculate standard deviation"""
        if not values:
            return 0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5

    def _empty_sentiment(self) -> Dict:
        """Return empty sentiment data"""
        return {
            'sentiment_score': 50,
            'sentiment_label': 'Neutral',
            'sentiment_emoji': '➡️',
            'win_rate': 0,
            'avg_pnl': 0,
            'momentum': 0,
            'total_trades_analyzed': 0
        }


def get_market_overview(db: Session, user_id: int) -> Dict:
    """
    Get overall market overview with AI insights

    Args:
        db: Database session
        user_id: User ID

    Returns:
        Market overview with insights
    """
    try:
        analyzer = AIAnalyzer(db, user_id)
        return analyzer.get_ai_insights()
    except Exception as e:
        logger.error(f"❌ Market overview failed: {str(e)}")
        return {}
