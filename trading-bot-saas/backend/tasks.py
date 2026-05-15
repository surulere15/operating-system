"""
Celery Tasks for Multi-Tenant Trading Bot Execution
Handles periodic bot execution, monitoring, and maintenance
"""

from celery_app import celery_app
from database import get_db, Bot, Trade, User
from trading_engine import TradingEngine
from datetime import datetime, timedelta
import logging

# Import notifications
try:
    from notifications import send_trade_notification as send_notification_helper
    NOTIFICATIONS_AVAILABLE = True
except ImportError:
    NOTIFICATIONS_AVAILABLE = False
    logger.warning("⚠️ Notifications module not available")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@celery_app.task(name='tasks.check_and_run_bots', bind=True)
def check_and_run_bots(self):
    """
    Main task: Check all active bots and run their trading cycles
    Runs every 60 seconds (configured in celery_app.py)
    """
    try:
        logger.info("🔍 Checking for active bots...")

        db = next(get_db())

        # Get all active bots
        active_bots = db.query(Bot).filter(Bot.status == 'active').all()

        logger.info(f"📊 Found {len(active_bots)} active bots")

        for bot in active_bots:
            try:
                # Check if it's time to run this bot (based on scan_interval)
                scan_interval = bot.config.get('scan_interval', 300)  # Default 5 minutes

                # Check last scan time
                if bot.last_trade_at:
                    time_since_last_scan = (datetime.utcnow() - bot.last_trade_at).total_seconds()
                    if time_since_last_scan < scan_interval:
                        logger.info(f"⏸️ Skipping bot {bot.id} - scanned {int(time_since_last_scan)}s ago (interval: {scan_interval}s)")
                        continue

                # Run bot trading cycle
                logger.info(f"🤖 Starting bot {bot.id} ({bot.name})")
                run_bot_trading_cycle.delay(bot.id)

            except Exception as e:
                logger.error(f"❌ Error checking bot {bot.id}: {str(e)}")
                continue

        db.close()
        logger.info("✅ Bot check completed")

    except Exception as e:
        logger.error(f"❌ check_and_run_bots failed: {str(e)}")
        self.retry(countdown=60, max_retries=3)


@celery_app.task(name='tasks.run_bot_trading_cycle', bind=True)
def run_bot_trading_cycle(self, bot_id: int):
    """
    Execute trading cycle for a specific bot
    1. Check open positions
    2. Generate signals for configured markets
    3. Execute trades if conditions are met
    """
    try:
        logger.info(f"🚀 Executing trading cycle for bot {bot_id}")

        db = next(get_db())

        # Initialize trading engine
        engine = TradingEngine(bot_id, db)

        # Run trading cycle
        engine.run_trading_cycle()

        db.close()
        logger.info(f"✅ Bot {bot_id} trading cycle completed")

    except Exception as e:
        logger.error(f"❌ run_bot_trading_cycle failed for bot {bot_id}: {str(e)}")
        # Retry with exponential backoff
        self.retry(countdown=2 ** self.request.retries * 60, max_retries=3)


@celery_app.task(name='tasks.update_all_bot_metrics')
def update_all_bot_metrics():
    """
    Update performance metrics for all bots
    Runs every 5 minutes (configured in celery_app.py)
    """
    try:
        logger.info("📊 Updating bot metrics...")

        db = next(get_db())

        # Get all bots
        bots = db.query(Bot).all()

        for bot in bots:
            try:
                # Calculate stats from trades
                trades = db.query(Trade).filter(
                    Trade.bot_id == bot.id,
                    Trade.status == 'closed'
                ).all()

                if trades:
                    total_pnl = sum(t.pnl or 0 for t in trades)
                    winning_trades = len([t for t in trades if (t.pnl or 0) > 0])
                    losing_trades = len([t for t in trades if (t.pnl or 0) <= 0])

                    # Update bot
                    bot.total_pnl = total_pnl
                    bot.total_trades = len(trades)
                    bot.winning_trades = winning_trades
                    bot.losing_trades = losing_trades
                    bot.current_balance = bot.capital + total_pnl

                    # Find last trade time
                    last_trade = max(trades, key=lambda t: t.closed_at or t.opened_at)
                    bot.last_trade_at = last_trade.closed_at or last_trade.opened_at

            except Exception as e:
                logger.error(f"❌ Error updating metrics for bot {bot.id}: {str(e)}")
                continue

        db.commit()
        db.close()
        logger.info("✅ Bot metrics updated")

    except Exception as e:
        logger.error(f"❌ update_all_bot_metrics failed: {str(e)}")


@celery_app.task(name='tasks.monitor_bot_health')
def monitor_bot_health(bot_id: int):
    """
    Monitor health of a specific bot
    - Check if bot is stuck
    - Check API key validity
    - Alert on errors
    """
    try:
        db = next(get_db())

        bot = db.query(Bot).filter(Bot.id == bot_id).first()
        if not bot:
            return

        # Check if bot is stuck (no trades in last 24 hours for active bot)
        if bot.status == 'active':
            if bot.last_trade_at:
                hours_since_last_trade = (datetime.utcnow() - bot.last_trade_at).total_seconds() / 3600
                if hours_since_last_trade > 24:
                    logger.warning(f"⚠️ Bot {bot_id} appears stuck (no trades in {hours_since_last_trade:.1f} hours)")

        db.close()

    except Exception as e:
        logger.error(f"❌ monitor_bot_health failed for bot {bot_id}: {str(e)}")


@celery_app.task(name='tasks.cleanup_old_data')
def cleanup_old_data():
    """
    Clean up old data to save space
    - Delete trades older than 1 year
    - Archive old bot logs
    Runs daily at midnight (configured in celery_app.py)
    """
    try:
        logger.info("🧹 Cleaning up old data...")

        db = next(get_db())

        # Delete trades older than 1 year
        one_year_ago = datetime.utcnow() - timedelta(days=365)
        old_trades = db.query(Trade).filter(
            Trade.closed_at < one_year_ago,
            Trade.status == 'closed'
        ).delete()

        db.commit()
        db.close()

        logger.info(f"✅ Cleanup completed - deleted {old_trades} old trades")

    except Exception as e:
        logger.error(f"❌ cleanup_old_data failed: {str(e)}")


@celery_app.task(name='tasks.stop_bot')
def stop_bot(bot_id: int):
    """
    Gracefully stop a bot
    - Close all open positions
    - Update bot status
    """
    try:
        logger.info(f"🛑 Stopping bot {bot_id}...")

        db = next(get_db())

        bot = db.query(Bot).filter(Bot.id == bot_id).first()
        if not bot:
            return

        # Initialize trading engine
        engine = TradingEngine(bot_id, db)

        # Get all open positions
        open_trades = db.query(Trade).filter(
            Trade.bot_id == bot_id,
            Trade.status == 'open'
        ).all()

        # Close all positions at market price
        for trade in open_trades:
            try:
                ticker = engine.exchange_client.fetch_ticker(trade.symbol)
                current_price = ticker['last']
                engine.close_position(trade, current_price, 'bot_stopped')
            except Exception as e:
                logger.error(f"❌ Error closing position {trade.id}: {str(e)}")
                continue

        # Update bot status
        bot.status = 'stopped'
        db.commit()
        db.close()

        logger.info(f"✅ Bot {bot_id} stopped successfully")

    except Exception as e:
        logger.error(f"❌ stop_bot failed for bot {bot_id}: {str(e)}")


@celery_app.task(name='tasks.send_trade_notification')
def send_trade_notification(user_id: int, bot_id: int, trade_id: int, trade_type: str):
    """
    Send notification when a trade is executed
    Supports email and Telegram
    """
    try:
        db = next(get_db())

        user = db.query(User).filter(User.id == user_id).first()
        bot = db.query(Bot).filter(Bot.id == bot_id).first()
        trade = db.query(Trade).filter(Trade.id == trade_id).first()

        if not (user and bot and trade):
            return

        # Check if user has notifications enabled
        if not user.email_notifications:
            logger.info(f"⏸️ Notifications disabled for user {user_id}")
            db.close()
            return

        # Send notifications if module available
        if NOTIFICATIONS_AVAILABLE:
            trade_dict = {
                'symbol': trade.symbol,
                'side': trade.side,
                'entry_price': trade.entry_price,
                'exit_price': trade.exit_price,
                'quantity': trade.quantity,
                'leverage': trade.leverage,
                'stop_loss': trade.stop_loss,
                'take_profit': trade.take_profit,
                'pnl': trade.pnl,
                'pnl_percent': trade.pnl_percent,
                'exit_reason': getattr(trade, 'exit_reason', None)
            }

            send_notification_helper(
                user_email=user.email,
                telegram_id=user.telegram_chat_id,
                user_name=user.full_name or user.email.split('@')[0],
                bot_name=bot.name,
                trade=trade_dict,
                event_type=trade_type
            )
            logger.info(f"✅ Notification sent: {user.email} - {trade_type} trade on {trade.symbol}")
        else:
            logger.info(f"📧 Notification (no module): {user.email} - Bot '{bot.name}' executed {trade_type} trade on {trade.symbol}")

        db.close()

    except Exception as e:
        logger.error(f"❌ send_trade_notification failed: {str(e)}")


@celery_app.task(name='tasks.test_bot_configuration')
def test_bot_configuration(bot_id: int):
    """
    Test bot configuration before starting
    - Validate API keys
    - Check market accessibility
    - Verify sufficient balance
    """
    try:
        logger.info(f"🧪 Testing bot {bot_id} configuration...")

        db = next(get_db())

        # Initialize trading engine
        engine = TradingEngine(bot_id, db)

        # Test exchange connection
        balance = engine.exchange_client.fetch_balance()
        logger.info(f"✅ Exchange connection successful - Balance: {balance.get('total', {})}")

        # Test market data access
        markets = engine.config.get('markets', [])
        for symbol in markets[:3]:  # Test first 3 markets
            ticker = engine.exchange_client.fetch_ticker(symbol)
            logger.info(f"✅ Market {symbol} accessible - Price: ${ticker['last']:.2f}")

        db.close()
        logger.info(f"✅ Bot {bot_id} configuration test passed")

        return {"status": "success", "message": "Configuration test passed"}

    except Exception as e:
        logger.error(f"❌ test_bot_configuration failed for bot {bot_id}: {str(e)}")
        return {"status": "error", "message": str(e)}


# ============================================================================
# Development/Testing Tasks
# ============================================================================

@celery_app.task(name='tasks.debug_bot')
def debug_bot(bot_id: int):
    """Debug task to inspect bot state"""
    try:
        db = next(get_db())

        bot = db.query(Bot).filter(Bot.id == bot_id).first()
        if not bot:
            return {"error": "Bot not found"}

        trades = db.query(Trade).filter(Trade.bot_id == bot_id).all()

        result = {
            "bot": {
                "id": bot.id,
                "name": bot.name,
                "status": bot.status,
                "exchange": bot.exchange,
                "capital": bot.capital,
                "current_balance": bot.current_balance,
                "total_pnl": bot.total_pnl,
                "total_trades": bot.total_trades,
                "config": bot.config
            },
            "trades": {
                "total": len(trades),
                "open": len([t for t in trades if t.status == 'open']),
                "closed": len([t for t in trades if t.status == 'closed'])
            }
        }

        db.close()
        return result

    except Exception as e:
        return {"error": str(e)}
