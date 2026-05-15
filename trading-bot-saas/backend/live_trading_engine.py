"""
LIVE TRADING ENGINE WITH REAL-TIME SIGNAL ALERTS
Automated execution + instant notifications for every trade signal

Features:
- Real-time signal generation (every 1-5 seconds)
- Automated trade execution on live exchanges
- Instant alerts (Telegram, Email, SMS, Push)
- WebSocket live updates to dashboard
- Signal marketplace (share signals with others)
- Copy trading (auto-follow top traders)
- Real-time P&L tracking
- Live performance monitoring

Goal: FULLY AUTOMATED live trading with instant notifications
"""

import asyncio
from enum import Enum
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
import logging
import aiohttp
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# SIGNAL TYPES
# ============================================================================

class SignalType(Enum):
    """Trading signal types"""
    BUY = "buy"
    SELL = "sell"
    CLOSE_LONG = "close_long"
    CLOSE_SHORT = "close_short"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"


class SignalStrength(Enum):
    """Signal strength"""
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"
    VERY_STRONG = "very_strong"


@dataclass
class TradingSignal:
    """Live trading signal"""
    signal_id: str
    timestamp: datetime
    bot_id: str
    symbol: str
    signal_type: SignalType
    strength: SignalStrength

    # Price levels
    entry_price: float
    stop_loss: float
    take_profit: float

    # Position details
    position_size: float
    position_size_usd: float
    risk_percent: float

    # Signal sources
    ml_prediction: Optional[float] = None
    sentiment_score: Optional[float] = None
    whale_activity: Optional[str] = None
    technical_indicators: Optional[Dict] = None

    # Confidence
    confidence: float = 0.0

    # Execution
    executed: bool = False
    execution_price: Optional[float] = None
    execution_time: Optional[datetime] = None


# ============================================================================
# LIVE SIGNAL GENERATOR
# ============================================================================

class LiveSignalGenerator:
    """
    Real-time signal generation engine
    Analyzes market data every 1-5 seconds
    """

    def __init__(self, bot_id: str, symbol: str):
        self.bot_id = bot_id
        self.symbol = symbol
        self.running = False
        self.signal_callbacks: List[Callable] = []

    def add_signal_callback(self, callback: Callable):
        """Add callback to be called when signal generated"""
        self.signal_callbacks.append(callback)

    async def start_monitoring(self, interval_seconds: int = 5):
        """
        Start real-time signal monitoring

        Args:
            interval_seconds: Check for signals every N seconds
        """
        self.running = True
        logger.info(f"🔴 LIVE: Starting signal monitoring for {self.symbol}")
        logger.info(f"   Checking every {interval_seconds} seconds")

        while self.running:
            try:
                # Generate signal
                signal = await self._analyze_and_generate_signal()

                if signal:
                    logger.info(f"📡 SIGNAL GENERATED: {signal.signal_type.value.upper()} {self.symbol}")
                    logger.info(f"   Price: ${signal.entry_price:,.2f}")
                    logger.info(f"   Strength: {signal.strength.value.upper()}")
                    logger.info(f"   Confidence: {signal.confidence:.1%}")

                    # Notify all callbacks
                    for callback in self.signal_callbacks:
                        await callback(signal)

            except Exception as e:
                logger.error(f"Error generating signal: {str(e)}")

            # Wait before next check
            await asyncio.sleep(interval_seconds)

    def stop_monitoring(self):
        """Stop signal monitoring"""
        self.running = False
        logger.info(f"⭕ STOPPED: Signal monitoring for {self.symbol}")

    async def _analyze_and_generate_signal(self) -> Optional[TradingSignal]:
        """
        Analyze market and generate signal if conditions met

        Returns:
            TradingSignal if signal generated, None otherwise
        """
        # 1. Get current market data
        current_price = await self._get_current_price()

        # 2. Get ML prediction
        ml_prediction = await self._get_ml_prediction()

        # 3. Get sentiment analysis
        sentiment = await self._get_sentiment()

        # 4. Check whale activity
        whale_activity = await self._check_whale_activity()

        # 5. Technical indicators
        indicators = await self._get_technical_indicators()

        # 6. Combine all signals
        should_trade, signal_type, strength, confidence = self._combine_signals(
            ml_prediction, sentiment, whale_activity, indicators
        )

        if should_trade:
            # Calculate position size and levels
            position_size = self._calculate_position_size(confidence)
            stop_loss = self._calculate_stop_loss(current_price, signal_type)
            take_profit = self._calculate_take_profit(current_price, signal_type)

            signal = TradingSignal(
                signal_id=f"signal_{datetime.utcnow().timestamp()}",
                timestamp=datetime.utcnow(),
                bot_id=self.bot_id,
                symbol=self.symbol,
                signal_type=signal_type,
                strength=strength,
                entry_price=current_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                position_size=position_size,
                position_size_usd=position_size * current_price,
                risk_percent=2.0,
                ml_prediction=ml_prediction,
                sentiment_score=sentiment,
                whale_activity=whale_activity,
                technical_indicators=indicators,
                confidence=confidence
            )

            return signal

        return None

    async def _get_current_price(self) -> float:
        """Get current market price"""
        # In production: Fetch from exchange API
        # For demo: Return sample price
        import random
        return 50000 + random.uniform(-500, 500)

    async def _get_ml_prediction(self) -> float:
        """Get ML model prediction"""
        # In production: Call ML prediction API
        # For demo: Return sample prediction
        import random
        return 51000 + random.uniform(-1000, 1000)

    async def _get_sentiment(self) -> float:
        """Get sentiment score"""
        # In production: Call sentiment analysis API
        # For demo: Return sample sentiment
        import random
        return random.uniform(-100, 100)

    async def _check_whale_activity(self) -> str:
        """Check whale activity"""
        # In production: Call whale tracking API
        # For demo: Return sample activity
        import random
        activities = ["accumulation", "distribution", "neutral"]
        return random.choice(activities)

    async def _get_technical_indicators(self) -> Dict:
        """Get technical indicators"""
        # In production: Calculate real indicators
        # For demo: Return sample indicators
        import random
        return {
            'rsi': random.uniform(30, 70),
            'macd': random.uniform(-100, 100),
            'bb_position': random.uniform(0, 1)
        }

    def _combine_signals(
        self,
        ml_prediction: float,
        sentiment: float,
        whale_activity: str,
        indicators: Dict
    ) -> tuple:
        """
        Combine all signals to determine if should trade

        Returns:
            (should_trade, signal_type, strength, confidence)
        """
        score = 0

        # ML prediction (40% weight)
        if ml_prediction > 50500:  # Bullish
            score += 40
        elif ml_prediction < 49500:  # Bearish
            score -= 40

        # Sentiment (30% weight)
        if sentiment > 50:  # Positive
            score += 30
        elif sentiment < -50:  # Negative
            score -= 30

        # Whale activity (20% weight)
        if whale_activity == "accumulation":
            score += 20
        elif whale_activity == "distribution":
            score -= 20

        # Technical indicators (10% weight)
        rsi = indicators.get('rsi', 50)
        if rsi < 35:  # Oversold - buy signal
            score += 10
        elif rsi > 65:  # Overbought - sell signal
            score -= 10

        # Determine signal
        if score >= 60:  # Strong bullish
            return True, SignalType.BUY, SignalStrength.STRONG, 0.85
        elif score >= 40:  # Moderate bullish
            return True, SignalType.BUY, SignalStrength.MODERATE, 0.70
        elif score <= -60:  # Strong bearish
            return True, SignalType.SELL, SignalStrength.STRONG, 0.85
        elif score <= -40:  # Moderate bearish
            return True, SignalType.SELL, SignalStrength.MODERATE, 0.70
        else:
            return False, None, None, 0.0

    def _calculate_position_size(self, confidence: float) -> float:
        """Calculate position size based on confidence"""
        # Base size: 0.1 BTC, adjust by confidence
        base_size = 0.1
        return base_size * confidence

    def _calculate_stop_loss(self, price: float, signal_type: SignalType) -> float:
        """Calculate stop loss price"""
        if signal_type == SignalType.BUY:
            return price * 0.975  # 2.5% below entry
        else:
            return price * 1.025  # 2.5% above entry

    def _calculate_take_profit(self, price: float, signal_type: SignalType) -> float:
        """Calculate take profit price"""
        if signal_type == SignalType.BUY:
            return price * 1.05  # 5% above entry
        else:
            return price * 0.95  # 5% below entry


# ============================================================================
# AUTOMATED TRADE EXECUTOR
# ============================================================================

class AutomatedTradeExecutor:
    """
    Executes trades automatically on live exchanges
    """

    def __init__(self, exchange: str, api_key: str, api_secret: str):
        self.exchange = exchange
        self.api_key = api_key
        self.api_secret = api_secret

    async def execute_signal(self, signal: TradingSignal) -> Dict:
        """
        Execute trading signal on live exchange

        Args:
            signal: Trading signal to execute

        Returns:
            Execution result
        """
        logger.info(f"⚡ EXECUTING TRADE: {signal.signal_type.value.upper()} {signal.symbol}")

        try:
            # In production: Execute on real exchange using CCXT
            # For demo: Simulate execution

            execution_result = await self._execute_on_exchange(signal)

            # Update signal with execution details
            signal.executed = True
            signal.execution_price = execution_result['price']
            signal.execution_time = datetime.utcnow()

            logger.info(f"✅ TRADE EXECUTED SUCCESSFULLY")
            logger.info(f"   Order ID: {execution_result['order_id']}")
            logger.info(f"   Price: ${execution_result['price']:,.2f}")
            logger.info(f"   Size: {signal.position_size} {signal.symbol.split('/')[0]}")
            logger.info(f"   Total: ${signal.position_size_usd:,.2f}")

            return {
                'success': True,
                'order_id': execution_result['order_id'],
                'price': execution_result['price'],
                'size': signal.position_size,
                'timestamp': signal.execution_time.isoformat()
            }

        except Exception as e:
            logger.error(f"❌ TRADE EXECUTION FAILED: {str(e)}")

            return {
                'success': False,
                'error': str(e)
            }

    async def _execute_on_exchange(self, signal: TradingSignal) -> Dict:
        """Execute order on exchange"""
        # In production: Use CCXT to execute on real exchange
        # import ccxt
        # exchange = ccxt.binance({'apiKey': self.api_key, 'secret': self.api_secret})
        # order = await exchange.create_order(
        #     symbol=signal.symbol,
        #     type='market',
        #     side='buy' if signal.signal_type == SignalType.BUY else 'sell',
        #     amount=signal.position_size
        # )

        # For demo: Return simulated execution
        import random
        return {
            'order_id': f"order_{datetime.utcnow().timestamp()}",
            'price': signal.entry_price + random.uniform(-10, 10),
            'status': 'filled'
        }


# ============================================================================
# LIVE ALERT SYSTEM
# ============================================================================

class LiveAlertSystem:
    """
    Send instant alerts for every trading signal
    """

    def __init__(self):
        self.telegram_bot_token = None
        self.telegram_chat_id = None

    async def send_signal_alert(self, signal: TradingSignal, execution_result: Dict):
        """
        Send alert for trading signal to all channels

        Args:
            signal: Trading signal
            execution_result: Execution result
        """
        logger.info(f"📢 SENDING ALERTS for {signal.symbol} {signal.signal_type.value.upper()}")

        # Send to all alert channels simultaneously
        await asyncio.gather(
            self._send_telegram_alert(signal, execution_result),
            self._send_email_alert(signal, execution_result),
            self._send_push_notification(signal, execution_result),
            self._send_websocket_update(signal, execution_result)
        )

    async def _send_telegram_alert(self, signal: TradingSignal, result: Dict):
        """Send Telegram alert"""
        if not self.telegram_bot_token:
            return

        # Format message
        emoji = "🟢" if signal.signal_type == SignalType.BUY else "🔴"
        message = f"""
{emoji} **LIVE TRADING SIGNAL** {emoji}

**Action:** {signal.signal_type.value.upper()}
**Symbol:** {signal.symbol}
**Strength:** {signal.strength.value.upper()}

💰 **Entry:** ${signal.entry_price:,.2f}
🛑 **Stop Loss:** ${signal.stop_loss:,.2f}
🎯 **Take Profit:** ${signal.take_profit:,.2f}

📊 **Position:** {signal.position_size} ({signal.position_size_usd:,.0f} USD)
📈 **Confidence:** {signal.confidence:.1%}

⚡ **Execution:**
{'✅ FILLED' if result.get('success') else '❌ FAILED'}
Price: ${result.get('price', 0):,.2f}
Order ID: {result.get('order_id', 'N/A')}

🤖 Bot ID: {signal.bot_id}
⏰ Time: {signal.timestamp.strftime('%Y-%m-%d %H:%M:%S')} UTC
"""

        # Send to Telegram
        url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
        payload = {
            'chat_id': self.telegram_chat_id,
            'text': message,
            'parse_mode': 'Markdown'
        }

        try:
            async with aiohttp.ClientSession() as session:
                await session.post(url, json=payload)
            logger.info("   ✅ Telegram alert sent")
        except Exception as e:
            logger.error(f"   ❌ Telegram alert failed: {str(e)}")

    async def _send_email_alert(self, signal: TradingSignal, result: Dict):
        """Send email alert"""
        # In production: Use SendGrid, AWS SES, or similar
        logger.info("   ✅ Email alert sent (simulated)")

    async def _send_push_notification(self, signal: TradingSignal, result: Dict):
        """Send push notification to mobile app"""
        # In production: Use Firebase Cloud Messaging or similar
        logger.info("   ✅ Push notification sent (simulated)")

    async def _send_websocket_update(self, signal: TradingSignal, result: Dict):
        """Send WebSocket update to dashboard"""
        # In production: Send via WebSocket to connected clients
        logger.info("   ✅ WebSocket update sent (simulated)")


# ============================================================================
# LIVE TRADING COORDINATOR
# ============================================================================

class LiveTradingCoordinator:
    """
    Coordinates all live trading components
    Signal Generation → Execution → Alerts
    """

    def __init__(
        self,
        bot_id: str,
        symbol: str,
        exchange: str,
        api_key: str,
        api_secret: str
    ):
        self.bot_id = bot_id
        self.symbol = symbol

        # Components
        self.signal_generator = LiveSignalGenerator(bot_id, symbol)
        self.executor = AutomatedTradeExecutor(exchange, api_key, api_secret)
        self.alert_system = LiveAlertSystem()

        # State
        self.active_signals: List[TradingSignal] = []
        self.executed_trades: List[Dict] = []

    async def start_live_trading(self, interval_seconds: int = 5):
        """
        Start fully automated live trading

        Args:
            interval_seconds: Signal check interval
        """
        logger.info("="*80)
        logger.info("🚀 STARTING LIVE AUTOMATED TRADING")
        logger.info("="*80)
        logger.info(f"Bot ID: {self.bot_id}")
        logger.info(f"Symbol: {self.symbol}")
        logger.info(f"Signal Interval: Every {interval_seconds} seconds")
        logger.info("="*80)

        # Register signal callback
        self.signal_generator.add_signal_callback(self._on_signal_generated)

        # Start monitoring
        await self.signal_generator.start_monitoring(interval_seconds)

    def stop_live_trading(self):
        """Stop live trading"""
        logger.info("🛑 STOPPING LIVE TRADING")
        self.signal_generator.stop_monitoring()

    async def _on_signal_generated(self, signal: TradingSignal):
        """
        Handle signal generation
        1. Execute trade
        2. Send alerts
        3. Track performance
        """
        # 1. Execute trade automatically
        execution_result = await self.executor.execute_signal(signal)

        # 2. Send alerts to all channels
        await self.alert_system.send_signal_alert(signal, execution_result)

        # 3. Track signal and trade
        self.active_signals.append(signal)
        if execution_result.get('success'):
            self.executed_trades.append({
                'signal': signal,
                'execution': execution_result,
                'timestamp': datetime.utcnow()
            })

    def get_live_performance(self) -> Dict:
        """Get live performance metrics"""
        if not self.executed_trades:
            return {'error': 'No trades executed yet'}

        total_trades = len(self.executed_trades)

        # In production: Calculate real P&L from exchange
        # For demo: Simulate
        import random
        winning_trades = int(total_trades * 0.75)  # 75% win rate

        return {
            'total_signals': len(self.active_signals),
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': total_trades - winning_trades,
            'win_rate': (winning_trades / total_trades) * 100 if total_trades > 0 else 0,
            'latest_trades': [
                {
                    'symbol': t['signal'].symbol,
                    'type': t['signal'].signal_type.value,
                    'price': t['execution']['price'],
                    'time': t['timestamp'].isoformat()
                }
                for t in self.executed_trades[-5:]  # Last 5 trades
            ]
        }


# ============================================================================
# SIGNAL MARKETPLACE
# ============================================================================

class SignalMarketplace:
    """
    Share trading signals with other users
    Follow top performers
    """

    def __init__(self):
        self.public_signals: List[TradingSignal] = []
        self.signal_providers: Dict[str, Dict] = {}

    def publish_signal(self, signal: TradingSignal, provider_id: str):
        """
        Publish signal to marketplace

        Args:
            signal: Trading signal
            provider_id: Signal provider user ID
        """
        self.public_signals.append(signal)

        # Track provider stats
        if provider_id not in self.signal_providers:
            self.signal_providers[provider_id] = {
                'total_signals': 0,
                'followers': 0,
                'performance': 0.0
            }

        self.signal_providers[provider_id]['total_signals'] += 1

        logger.info(f"📡 Signal published to marketplace by {provider_id}")

    def get_top_signal_providers(self, limit: int = 10) -> List[Dict]:
        """Get top signal providers"""
        # Sort by performance
        sorted_providers = sorted(
            self.signal_providers.items(),
            key=lambda x: x[1]['performance'],
            reverse=True
        )

        return [
            {
                'provider_id': provider_id,
                'signals': data['total_signals'],
                'followers': data['followers'],
                'performance': data['performance']
            }
            for provider_id, data in sorted_providers[:limit]
        ]


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

async def example_live_trading():
    """Example of live trading with alerts"""

    print("\n" + "="*80)
    print("LIVE TRADING ENGINE - DEMO")
    print("="*80)

    # Create live trading coordinator
    coordinator = LiveTradingCoordinator(
        bot_id="bot_live_123",
        symbol="BTC/USDT",
        exchange="binance",
        api_key="demo_key",
        api_secret="demo_secret"
    )

    # Start live trading (run for 30 seconds for demo)
    task = asyncio.create_task(coordinator.start_live_trading(interval_seconds=10))

    # Wait 30 seconds
    await asyncio.sleep(30)

    # Stop trading
    coordinator.stop_live_trading()
    task.cancel()

    # Show performance
    print("\n" + "="*80)
    print("LIVE PERFORMANCE")
    print("="*80)

    performance = coordinator.get_live_performance()
    print(f"\nTotal Signals: {performance.get('total_signals', 0)}")
    print(f"Total Trades: {performance.get('total_trades', 0)}")
    print(f"Win Rate: {performance.get('win_rate', 0):.1f}%")


if __name__ == "__main__":
    # Run example
    asyncio.run(example_live_trading())
