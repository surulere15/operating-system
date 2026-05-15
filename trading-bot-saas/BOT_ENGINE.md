# 🤖 Trading Bot Engine Documentation

**Multi-tenant Celery-based trading bot execution system**

---

## 📖 **Overview**

The Trading Bot Engine is a sophisticated multi-tenant system that executes automated trading strategies for all users simultaneously. Built with Celery, Redis, and CCXT, it handles:

- ✅ **Multi-tenant execution** - Run 100s of bots concurrently
- ✅ **Real-time trading** - Execute trades on 6+ exchanges
- ✅ **Risk management** - Automated stop-loss, take-profit, position sizing
- ✅ **Signal generation** - Technical analysis (MA crossover, RSI, volume)
- ✅ **Performance monitoring** - Track P&L, win rate, trade history
- ✅ **Fault tolerance** - Auto-retry, error handling, graceful shutdown

---

## 🏗️ **Architecture**

```
┌─────────────────────────────────────────────────────────────┐
│                     Trading Bot Engine                       │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐    │
│  │ Celery Beat  │──▶│ Celery Worker│──▶│   Trading    │    │
│  │  Scheduler   │   │    (x4)      │   │   Engine     │    │
│  └──────────────┘   └──────────────┘   └──────────────┘    │
│         │                  │                    │            │
│         │                  │                    │            │
│         ▼                  ▼                    ▼            │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐    │
│  │   Redis      │   │  PostgreSQL  │   │   CCXT       │    │
│  │  (Queue)     │   │  (Database)  │   │ (Exchanges)  │    │
│  └──────────────┘   └──────────────┘   └──────────────┘    │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### **Components:**

1. **Celery Beat** - Periodic task scheduler (runs every 60 seconds)
2. **Celery Worker** - Executes trading tasks (4 concurrent workers)
3. **Trading Engine** - Core trading logic (signals, risk, execution)
4. **Redis** - Message queue and result backend
5. **PostgreSQL** - Persistent storage (bots, trades, users)
6. **CCXT** - Exchange API integration (6+ exchanges)

---

## 🚀 **Getting Started**

### **Prerequisites:**

```bash
# 1. Install dependencies
cd backend
pip install -r requirements.txt

# 2. Start Redis
brew services start redis  # macOS
sudo systemctl start redis  # Linux

# 3. Start PostgreSQL (should already be running)
brew services start postgresql  # macOS
sudo systemctl start postgresql  # Linux

# 4. Create logs directory
mkdir -p logs
```

### **Start the Bot Engine:**

```bash
# Method 1: Using startup script (recommended)
./start_bot_engine.sh

# Method 2: Manual startup
celery -A celery_app worker --loglevel=info --concurrency=4 &
celery -A celery_app beat --loglevel=info &
```

### **Verify It's Running:**

```bash
# Check worker status
celery -A celery_app inspect active

# Check scheduled tasks
celery -A celery_app inspect scheduled

# Monitor with Flower (Web UI)
celery -A celery_app flower
# Visit: http://localhost:5555
```

---

## 📊 **How It Works**

### **1. Bot Activation Flow**

```
User clicks "Start Bot" in UI
        ↓
FastAPI endpoint: POST /api/bots/{id}/start
        ↓
Update bot.status = 'active' in database
        ↓
Celery Beat picks up active bot (next cycle)
        ↓
Trading Engine runs trading cycle
        ↓
Trades executed on exchange
        ↓
Results saved to database
        ↓
UI updates in real-time
```

### **2. Trading Cycle (per bot)**

Every bot runs this cycle based on its `scan_interval` (default: 5 minutes):

```python
1. Check Open Positions
   - Fetch current market price
   - Check if stop-loss hit → Close position
   - Check if take-profit hit → Close position
   - Update P&L in database

2. Generate Signals (for each market)
   - Fetch OHLCV data (15-min candles, 100 bars)
   - Calculate indicators:
     * SMA Fast (9 periods)
     * SMA Slow (21 periods)
     * RSI (14 periods)
     * Volume analysis
   - Detect crossovers:
     * Bullish: Fast MA crosses above Slow MA
     * Bearish: Fast MA crosses below Slow MA
   - Calculate confidence (0-100%):
     * Base: 50% (crossover detected)
     * +20-30% (RSI confirmation)
     * +15% (volume confirmation)

3. Execute Trades (if signal confidence > threshold)
   - Check risk limits:
     * Daily loss < max_daily_loss (default: 10%)
     * Open positions < 5
     * Balance > $10
   - Calculate position size:
     * Use 20% of available capital
     * Apply leverage (default: 15x)
   - Place market order with:
     * Stop-loss (default: 3% from entry)
     * Take-profit (5% from entry)
   - Save trade to database
```

### **3. Risk Management**

**Position Sizing:**
```python
capital_per_trade = current_balance * 0.20  # Use 20% per trade
position_value = capital_per_trade * leverage  # Apply leverage
quantity = position_value / current_price  # Calculate quantity
```

**Stop Loss:**
```python
# For BUY orders
stop_loss = entry_price * (1 - max_position_loss/100)  # 3% below entry

# For SELL orders
stop_loss = entry_price * (1 + max_position_loss/100)  # 3% above entry
```

**Take Profit:**
```python
# For BUY orders
take_profit = entry_price * 1.05  # 5% profit target

# For SELL orders
take_profit = entry_price * 0.95  # 5% profit target
```

**Daily Loss Limit:**
```python
today_pnl_percent = (today_pnl / capital) * 100
if today_pnl_percent <= -max_daily_loss:
    # Stop trading for the day
    pass
```

---

## 📈 **Trading Strategy**

### **Current Strategy: MA Crossover + RSI + Volume**

**Indicators:**
- **SMA Fast (9)** - Short-term trend
- **SMA Slow (21)** - Long-term trend
- **RSI (14)** - Momentum (overbought/oversold)
- **Volume** - Confirmation

**Entry Signals:**

**BULLISH (BUY):**
```
Conditions:
1. Fast MA crosses ABOVE Slow MA (golden cross)
2. RSI between 30-70 (not overbought) OR
   RSI < 30 (oversold - stronger signal)
3. Volume > 120% of 20-period average (confirmation)

Confidence Calculation:
- Base: 50% (crossover detected)
- +20% if RSI neutral (30-70)
- +30% if RSI oversold (< 30)
- +15% if strong volume
- Maximum: 100%
```

**BEARISH (SELL):**
```
Conditions:
1. Fast MA crosses BELOW Slow MA (death cross)
2. RSI between 30-70 (not oversold) OR
   RSI > 70 (overbought - stronger signal)
3. Volume > 120% of 20-period average (confirmation)

Confidence Calculation:
- Base: 50% (crossover detected)
- +20% if RSI neutral (30-70)
- +30% if RSI overbought (> 70)
- +15% if strong volume
- Maximum: 100%
```

**Example Trade:**
```
Market: BTC/USDT
Price: $65,000

Signal Generated:
- Fast MA: $65,200 (crossed above Slow MA)
- Slow MA: $64,800
- RSI: 45 (neutral)
- Volume: 150% of average
- Confidence: 50 + 20 + 15 = 85%

Threshold: 60% (configured)
Result: ✅ Execute BUY

Trade Execution:
- Side: BUY
- Entry: $65,000
- Quantity: 0.046 BTC (15x leverage, $35 capital)
- Stop Loss: $63,050 (3% below entry)
- Take Profit: $68,250 (5% above entry)

Outcome Scenarios:
1. ✅ Take Profit Hit: +$1.73 profit (+5%)
2. ❌ Stop Loss Hit: -$1.05 loss (-3%)
3. ⏸️ Signal reversal: Close at market
```

---

## ⚙️ **Configuration**

### **Bot Configuration (per bot):**

```json
{
  "markets": ["BTC/USDT", "ETH/USDT", "SOL/USDT"],
  "leverage": {
    "BTC/USDT": 15,
    "ETH/USDT": 15,
    "SOL/USDT": 20
  },
  "confidence_threshold": 60,     // Min confidence to trade (0-100)
  "max_daily_loss": 10,           // Stop if daily loss exceeds (%)
  "max_position_loss": 3,         // Stop loss per trade (%)
  "scan_interval": 300            // Seconds between scans (5 min)
}
```

### **Celery Configuration:**

**Performance:**
```python
worker_concurrency = 4              # 4 parallel workers
worker_prefetch_multiplier = 1      # 1 task per worker
task_acks_late = True               # Acknowledge after completion
worker_max_tasks_per_child = 1000   # Restart worker after 1000 tasks
```

**Timeouts:**
```python
task_soft_time_limit = 300   # 5 minutes soft limit
task_time_limit = 360        # 6 minutes hard limit
```

**Retry:**
```python
task_default_retry_delay = 60   # Wait 60s before retry
task_max_retries = 3            # Maximum 3 retry attempts
```

### **Scheduled Tasks:**

| Task | Frequency | Description |
|------|-----------|-------------|
| `check_and_run_bots` | Every 60s | Find active bots and run trading cycles |
| `update_all_bot_metrics` | Every 5 min | Recalculate P&L, win rate, etc. |
| `cleanup_old_data` | Daily (midnight) | Delete trades older than 1 year |

---

## 🧪 **Testing**

### **Test Bot Configuration:**

```python
from tasks import test_bot_configuration

# Test bot before starting
result = test_bot_configuration.delay(bot_id=1)
print(result.get())

# Output:
# {
#   "status": "success",
#   "message": "Configuration test passed"
# }
```

### **Debug Bot State:**

```python
from tasks import debug_bot

# Inspect bot state
result = debug_bot.delay(bot_id=1)
print(result.get())

# Output:
# {
#   "bot": {
#     "id": 1,
#     "name": "My Bot",
#     "status": "active",
#     "total_pnl": 1.30,
#     ...
#   },
#   "trades": {
#     "total": 5,
#     "open": 1,
#     "closed": 4
#   }
# }
```

### **Manual Trade Execution:**

```python
from trading_engine import TradingEngine
from database import get_db

db = next(get_db())
engine = TradingEngine(bot_id=1, db=db)

# Generate signal
signal = engine.generate_signal('BTC/USDT')
print(signal)
# {'action': 'buy', 'confidence': 85, 'reason': 'Bullish crossover. RSI neutral, Strong volume'}

# Execute trade
trade = engine.execute_trade('BTC/USDT', 'buy', 85)
print(f"Trade executed: {trade.id}")
```

---

## 📋 **Monitoring**

### **Celery Flower (Web UI):**

```bash
# Start Flower
celery -A celery_app flower

# Visit: http://localhost:5555

Features:
- Real-time task monitoring
- Worker status and stats
- Task history and results
- Performance graphs
```

### **Log Files:**

```bash
# Worker logs
tail -f logs/celery_worker.log

# Beat scheduler logs
tail -f logs/celery_beat.log

# Filter for specific bot
grep "bot 1" logs/celery_worker.log
```

### **Database Queries:**

```sql
-- Check active bots
SELECT id, name, status, total_trades, total_pnl
FROM bots
WHERE status = 'active';

-- Check recent trades
SELECT * FROM trades
WHERE opened_at > NOW() - INTERVAL '1 hour'
ORDER BY opened_at DESC;

-- Check bot performance
SELECT
  b.name,
  COUNT(t.id) as total_trades,
  SUM(CASE WHEN t.pnl > 0 THEN 1 ELSE 0 END) as wins,
  SUM(t.pnl) as total_pnl
FROM bots b
LEFT JOIN trades t ON b.id = t.bot_id
WHERE t.status = 'closed'
GROUP BY b.id;
```

---

## 🛑 **Stopping the Engine**

### **Graceful Shutdown:**

```bash
# Method 1: If using startup script
# Press Ctrl+C in the terminal

# Method 2: Kill processes
pkill -f 'celery worker'
pkill -f 'celery beat'

# Method 3: Kill specific PIDs
kill $(cat logs/celery_worker.pid)
kill $(cat logs/celery_beat.pid)
```

**What happens on shutdown:**
- ✅ Current tasks complete
- ✅ No new tasks accepted
- ✅ Open positions remain open (managed by exchange stop-loss/take-profit)
- ✅ Bot status remains 'active' (will resume on restart)

### **Emergency Stop (with position closure):**

```python
from tasks import stop_bot

# Close all positions and stop bot
stop_bot.delay(bot_id=1)

# This will:
# 1. Close all open positions at market price
# 2. Update bot status to 'stopped'
# 3. Save final P&L to database
```

---

## 🔧 **Troubleshooting**

### **Problem: Redis connection failed**

```bash
# Check Redis status
redis-cli ping
# Should return: PONG

# Start Redis if not running
brew services start redis  # macOS
sudo systemctl start redis  # Linux
```

### **Problem: Worker not processing tasks**

```bash
# Check worker status
celery -A celery_app inspect active

# Check if tasks are queued
celery -A celery_app inspect scheduled

# Restart worker
pkill -f 'celery worker'
celery -A celery_app worker --loglevel=info --concurrency=4
```

### **Problem: Bot appears stuck**

```python
# Check bot state
from tasks import debug_bot
result = debug_bot.delay(bot_id=1)
print(result.get())

# Check logs
# tail -f logs/celery_worker.log | grep "bot 1"

# Restart bot
# 1. Stop bot in UI
# 2. Wait 60 seconds
# 3. Start bot in UI
```

### **Problem: Trades not executing**

**Common causes:**
1. **Low confidence** - Check signal confidence vs threshold
2. **Risk limits hit** - Daily loss exceeded or too many open positions
3. **Insufficient balance** - Need minimum $10
4. **API key invalid** - Test connection on API Keys page
5. **Exchange issues** - Check exchange status

**Debug steps:**
```python
from trading_engine import TradingEngine
from database import get_db

db = next(get_db())
engine = TradingEngine(bot_id=1, db=db)

# 1. Check risk limits
can_trade, reason = engine.check_risk_limits()
print(f"Can trade: {can_trade}, Reason: {reason}")

# 2. Generate signal
signal = engine.generate_signal('BTC/USDT')
print(f"Signal: {signal}")

# 3. Check threshold
threshold = engine.config.get('confidence_threshold', 60)
print(f"Threshold: {threshold}%")
```

---

## 📊 **Performance**

### **Current Capacity:**

| Metric | Value |
|--------|-------|
| **Concurrent Bots** | 100+ |
| **Concurrent Workers** | 4 |
| **Tasks per Minute** | ~60 (1 per bot per minute) |
| **Average Task Duration** | 5-10 seconds |
| **Exchanges Supported** | 6 live, 100+ available |

### **Scaling:**

**Horizontal Scaling:**
```bash
# Add more workers
celery -A celery_app worker --concurrency=8  # 8 workers instead of 4

# Or run multiple worker instances
celery -A celery_app worker -n worker1@%h &
celery -A celery_app worker -n worker2@%h &
```

**Vertical Scaling:**
```python
# Adjust Celery config in celery_app.py
worker_concurrency = 8  # Increase from 4 to 8
```

---

## 🔐 **Security**

### **API Key Encryption:**

All API keys are encrypted in the database using Fernet (AES-256):

```python
from cryptography.fernet import Fernet
from database import encrypt_value, decrypt_value

# Encryption happens automatically
api_key_obj.api_key = encrypt_value(api_key)  # Stored encrypted

# Decryption happens in TradingEngine
api_key = decrypt_value(api_key_obj.api_key)  # Decrypted for use
```

### **Best Practices:**

✅ **Never log API keys** - Only log encrypted versions
✅ **Use testnet first** - Test with fake money before live trading
✅ **Disable withdrawals** - API keys should NEVER have withdrawal permissions
✅ **IP whitelist** - Restrict API keys to known IPs
✅ **Rotate keys monthly** - Generate new API keys regularly
✅ **Monitor unusual activity** - Alert on unexpected trades

---

## 📚 **Additional Resources**

- **Celery Documentation**: https://docs.celeryproject.org
- **CCXT Documentation**: https://docs.ccxt.com
- **Redis Documentation**: https://redis.io/docs
- **Technical Analysis**: https://www.investopedia.com/terms/t/technicalanalysis.asp

---

## 🆘 **Support**

**Need help?**
- Check logs: `tail -f logs/celery_worker.log`
- Use debug tools: `debug_bot.delay(bot_id)`
- Test configuration: `test_bot_configuration.delay(bot_id)`
- Report issues: GitHub Issues

---

**Last Updated:** 2026-02-11
**Version:** 1.0.0
**Status:** ✅ Production Ready
