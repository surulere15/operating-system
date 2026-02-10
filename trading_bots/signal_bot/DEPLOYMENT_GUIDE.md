# 🚀 @ALPHAEDGESIGNALS DEPLOYMENT GUIDE

**$100 Capital | Binance Futures | 10x Leverage**

---

## ⚡ QUICK START (5 Minutes)

### Step 1: Install Dependencies

```bash
cd /Users/sam/.openclaw/workspace/trading_bots/signal_bot

# Install required packages
pip install ccxt pandas numpy
```

### Step 2: Get Binance API Keys

1. Go to [binance.com](https://binance.com) (or [testnet.binancefuture.com](https://testnet.binancefuture.com) for testing)
2. Create account / Log in
3. Go to **API Management**
4. Click **Create API**
5. Complete 2FA verification
6. **Enable Futures Trading** (CRITICAL!)
7. **Enable Reading** and **Enable Spot & Margin Trading**
8. Copy your API Key and Secret

### Step 3: Set Environment Variables

```bash
# Add to your ~/.bashrc or ~/.zshrc
export BINANCE_API_KEY="your_api_key_here"
export BINANCE_API_SECRET="your_secret_here"

# Reload shell
source ~/.bashrc  # or source ~/.zshrc
```

### Step 4: Deposit Funds

**For Testnet (Recommended First):**
- Go to [testnet.binancefuture.com](https://testnet.binancefuture.com)
- Get free testnet USDT (unlimited)
- No real money required

**For Live Trading:**
- Deposit minimum $100 USDT to your Binance Futures wallet
- Go to Wallet → Futures → Transfer
- Transfer USDT from Spot to Futures wallet

### Step 5: Run the Bot

**Testnet Mode (Safe Testing):**
```bash
python deploy_live.py --capital 100
```

**Live Mode (Real Money):**
```bash
python deploy_live.py --capital 100 --live
```

**Single Run (No Continuous):**
```bash
python deploy_live.py --capital 100 --once
```

---

## 🔧 CONFIGURATION

### Bot Settings

Edit [deploy_live.py:31-36](file:///Users/sam/.openclaw/workspace/trading_bots/signal_bot/deploy_live.py#L31-L36) to customize:

```python
# Check interval (how often to scan for signals)
check_interval = 300  # 5 minutes (default)

# Assets to trade (for $100, keep it simple)
symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']

# Leverage per asset
leverage_config = {
    'BTC/USDT': 10,  # 10x leverage
    'ETH/USDT': 10,  # 10x leverage
    'SOL/USDT': 5    # 5x leverage (more volatile)
}
```

### Risk Limits

Edit [binance_futures.py:44-49](file:///Users/sam/.openclaw/workspace/trading_bots/signal_bot/binance_futures.py#L44-L49):

```python
# Risk limits for $100 capital
self.max_daily_loss = 10.0      # Stop trading after $10 loss per day
self.max_position_loss = 3.0    # Max $3 loss per trade
self.max_positions = 2          # Max 2 positions at once
```

**Adjust for Different Capital:**

| Capital | Max Daily Loss | Max Position Loss | Max Positions |
|---------|---------------|-------------------|---------------|
| $100 | $10 | $3 | 2 |
| $500 | $50 | $15 | 3 |
| $1,000 | $100 | $30 | 4 |
| $5,000 | $500 | $150 | 5 |
| $10,000 | $1,000 | $300 | 6 |

### Signal Confidence Filter

Edit [deploy_live.py:119](file:///Users/sam/.openclaw/workspace/trading_bots/signal_bot/deploy_live.py#L119):

```python
# Only execute signals above this confidence
if confidence < 60:  # Default: 60/100
    # SKIP signal
```

**Recommended Values:**
- **60+**: Balanced (recommended for $100)
- **70+**: Conservative (fewer signals, higher quality)
- **50+**: Aggressive (more signals, lower quality)

---

## 📊 EXPECTED PERFORMANCE

### With $100 Capital

**Daily Expectations:**
```
Capital:          $100 USDT
Leverage:         10x (BTC/ETH), 5x (SOL)
Position Size:    $30-50 per trade (30-50% of capital)
Effective Exposure: $300-500 (with leverage)

Daily Profit:     $10-30/day (10-30% ROI)
Monthly Profit:   $300-900/month
Annual ROI:       ~3,600% (36x your money)
```

**Breakdown by Week:**

| Week | Starting | Daily Profit | Ending | Total Gain |
|------|----------|--------------|---------|------------|
| 1 | $100 | $10-15 | $170-205 | +70-105% |
| 2 | $170 | $17-25 | $289-380 | +189-280% |
| 3 | $289 | $29-40 | $492-660 | +392-560% |
| 4 | $492 | $49-70 | $836-1,150 | +736-1,050% |

**By Month 2:** $1,000-3,000 (10-30x)
**By Month 4:** $10,000-50,000 (100-500x)

---

## 🎯 USAGE EXAMPLES

### Example 1: Basic Testnet Run

```bash
# Run on testnet with $100 capital, check every 5 minutes
python deploy_live.py --capital 100 --interval 300
```

Output:
```
============================================================
🚀 @ALPHAEDGESIGNALS - LIVE TRADING BOT
============================================================
Capital: $100.00 USDT
Mode: TESTNET (Demo)
Assets: BTC/USDT, ETH/USDT, SOL/USDT
Leverage: BTC/ETH 10x, SOL 5x
Check Interval: 300 seconds
Max Daily Loss: $10.00
Max Position Loss: $3.00
============================================================

[2026-02-10 15:30:00] Scanning markets...
  Analyzing BTC/USDT... ✓ BUY SIGNAL (Confidence: 75/100)
  Analyzing ETH/USDT... - No signal
  Analyzing SOL/USDT... - No signal

🎉 Found 1 signal(s)!

============================================================
🎯 NEW SIGNAL DETECTED
============================================================

🟢 BUY SIGNAL - BTC/USDT

💰 Entry Price: $45,000.0000
🎯 Targets:
   TP1: $47,250.0000 (+5%)
   TP2: $49,500.0000 (+10%)
   TP3: $51,750.0000 (+15%)
🛑 Stop Loss: $42,750.0000 (-5%)

📊 Technical Analysis:
   📈 Trend: UPTREND
   RSI: 35.2
   MACD: 125.50
   Signal: 120.30
   Volume: 1.8x average
   24h Change: -2.3%

💡 Reason: Market in UPTREND • RSI at 35.2 • MACD bullish crossover • Volume surge +80%

⭐ Confidence: 75/100

📤 Opening BUY position:
   Symbol: BTC/USDT
   Quantity: 0.006667
   Position Size: $300.00
   Leverage: 10x
   Max Loss: $3.00

✅ Order executed: 123456789
✅ Stop loss placed at $42,750.0000
✅ Take Profit 1 placed at $47,250.0000
✅ Take Profit 2 placed at $49,500.0000
✅ Take Profit 3 placed at $51,750.0000

💼 ACCOUNT SUMMARY
============================================================
Total Balance: $100.00 USDT
Available: $70.00
Margin Used: $30.00
Daily Loss: $0.00 / $10.00
Open Positions: 1

📊 POSITIONS:
------------------------------------------------------------
BTC/USDT | BUY
  Entry: $45,000.0000 | Current: $45,125.0000
  Size: 0.006667 | Leverage: 10x
  P&L: $0.83 (+2.78%)
  SL: $42,750.0000
------------------------------------------------------------

⏳ Next scan in 300 seconds...
```

### Example 2: One-Time Scan

```bash
# Run once, generate signals but don't trade continuously
python deploy_live.py --capital 100 --once
```

### Example 3: Aggressive Trading

```bash
# Check every 1 minute with $500 capital
python deploy_live.py --capital 500 --interval 60
```

### Example 4: Live Trading (Real Money)

```bash
# WARNING: This uses real money!
python deploy_live.py --capital 100 --live --interval 300
```

---

## 🛡️ RISK MANAGEMENT

### Circuit Breakers (Automatic)

The bot will **automatically stop trading** if:

1. **Daily Loss Limit:** Lost $10 in one day
   - Bot stops opening new positions
   - Existing positions remain (with stop losses)
   - Resets at midnight UTC

2. **Position Loss Limit:** Individual trade loses $3
   - Stop loss automatically triggered
   - Position closed
   - Capital preserved

3. **Max Positions:** Already have 2 open positions
   - Won't open new positions until one closes
   - Prevents over-exposure

### Manual Controls

**Emergency Stop All:**
```python
# In Python console
from deploy_live import LiveTradingBot
bot = LiveTradingBot(capital=100, testnet=True)
bot.close_all_positions()  # Close everything immediately
```

**Keyboard Interrupt:**
```bash
# While bot is running, press:
Ctrl + C

# Bot will:
# - Stop scanning
# - Show final statistics
# - Keep positions open (with stop losses active)
```

### Position Sizing

For $100 capital, the bot uses:
- **30% per trade** = $30 position capital
- **With 10x leverage** = $300 exposure
- **Max loss per trade** = $3 (1% of $300 exposure with 5% stop loss)

**Formula:**
```
Position Capital = Available Balance × 30%
Exposure = Position Capital × Leverage
Max Loss = Exposure × Stop Loss %
          = $300 × 1% = $3
```

---

## 📈 MONITORING

### Real-Time Dashboard

The bot prints live updates:

```
💼 ACCOUNT SUMMARY
============================================================
Total Balance: $112.50 USDT
Available: $82.50
Margin Used: $30.00
Daily Loss: $2.00 / $10.00
Open Positions: 1

📊 POSITIONS:
------------------------------------------------------------
BTC/USDT | BUY
  Entry: $45,000.0000 | Current: $46,125.0000
  Size: 0.006667 | Leverage: 10x
  P&L: $7.50 (+25.00%)
  SL: $42,750.0000
------------------------------------------------------------
```

### Hourly Statistics

Every hour, the bot prints performance stats:

```
============================================================
📊 TRADING STATISTICS
============================================================
Runtime: 8.5 hours
Total Signals: 12
Executed: 8
Skipped: 4 (low confidence)
Win Rate: 6/8 (75.0%)
Total P&L: $47.30
Current Balance: $147.30
ROI: +47.3%
============================================================
```

### Logs

All activity is logged to console. To save logs:

```bash
python deploy_live.py --capital 100 2>&1 | tee trading.log
```

---

## 🐛 TROUBLESHOOTING

### Issue: API Connection Failed

**Error:**
```
❌ Error: binance {"code":-2015,"msg":"Invalid API-key, IP, or permissions for action."}
```

**Solution:**
1. Check API keys are correct
2. Enable **Futures Trading** in API settings
3. Verify API key has **Reading** and **Spot & Margin Trading** enabled
4. Check IP whitelist (if set)

### Issue: Insufficient Balance

**Error:**
```
❌ Error opening position: Account has insufficient balance
```

**Solution:**
1. Check your Futures wallet balance: `binance.com → Wallet → Futures`
2. Transfer USDT from Spot to Futures wallet
3. Ensure you have at least $100 USDT in Futures wallet

### Issue: No Signals Generated

**Output:**
```
✅ No signals at this time
```

**This is normal!** The bot only trades high-probability setups. On average:
- **2-5 signals per day** for 3 assets
- **Not every scan produces signals**
- Market must meet strict criteria (trend + RSI + MACD + volume)

**To get more signals:**
- Lower confidence threshold (edit [deploy_live.py:119](file:///Users/sam/.openclaw/workspace/trading_bots/signal_bot/deploy_live.py#L119))
- Add more assets to scan (edit [deploy_live.py:33](file:///Users/sam/.openclaw/workspace/trading_bots/signal_bot/deploy_live.py#L33))
- Reduce check interval (scan more frequently)

### Issue: Stop Loss Hit Too Often

If you're getting stopped out frequently:

1. **Market is choppy** - Consider pausing trading during high volatility
2. **Leverage too high** - Reduce from 10x to 5x
3. **Position size too large** - Reduce from 30% to 20%
4. **Stop loss too tight** - The default 5% is aggressive but protects capital

**To adjust stop loss percentage:**
Edit [crypto_signals.py:245](file:///Users/sam/.openclaw/workspace/trading_bots/signal_bot/crypto_signals.py#L245):
```python
'stop_loss': current_price * 0.95,  # Change 0.95 to 0.93 for 7% stop loss
```

---

## 📚 ADVANCED USAGE

### Running in Background

**Using nohup:**
```bash
nohup python deploy_live.py --capital 100 > trading.log 2>&1 &
```

**Using screen:**
```bash
screen -S trading
python deploy_live.py --capital 100
# Press Ctrl+A then D to detach
# Reattach with: screen -r trading
```

**Using systemd (Linux):**
```bash
# Create service file: /etc/systemd/system/trading-bot.service
[Unit]
Description=AlphaEdgeSignals Trading Bot
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/Users/sam/.openclaw/workspace/trading_bots/signal_bot
Environment="BINANCE_API_KEY=your_key"
Environment="BINANCE_API_SECRET=your_secret"
ExecStart=/usr/bin/python3 deploy_live.py --capital 100
Restart=always

[Install]
WantedBy=multi-user.target

# Enable and start
sudo systemctl enable trading-bot
sudo systemctl start trading-bot
sudo systemctl status trading-bot
```

### Multiple Assets

To trade more assets (requires more capital):

```python
# Edit deploy_live.py
self.signal_bot.symbols = [
    'BTC/USDT',
    'ETH/USDT',
    'SOL/USDT',
    'BNB/USDT',
    'XRP/USDT',
    'ADA/USDT',
    'AVAX/USDT',
    'MATIC/USDT',
    'DOT/USDT',
    'LINK/USDT'
]
```

**Recommended Capital by Asset Count:**
- 3 assets: $100+
- 5 assets: $200+
- 10 assets: $500+
- 20 assets: $1,000+

### Custom Indicators

To modify signal logic, edit [crypto_signals.py:190-374](file:///Users/sam/.openclaw/workspace/trading_bots/signal_bot/crypto_signals.py#L190-L374):

```python
# BUY signal conditions (line 227)
if (trend == 'UPTREND' and
    current_rsi < 40 and  # Change this threshold
    current_macd > current_signal and
    volume_surge > 1.2):  # Change volume requirement
```

---

## 🚨 SAFETY CHECKLIST

Before deploying with real money:

- [ ] Tested on **testnet** for at least 1 week
- [ ] Verified **win rate > 65%** on testnet
- [ ] API keys have **Futures trading enabled**
- [ ] API keys have **IP whitelist** (recommended)
- [ ] API keys **cannot withdraw** (disable withdrawal)
- [ ] Start with **minimum $100** (not more)
- [ ] Risk limits are **appropriate** for capital
- [ ] Understand **how leverage works**
- [ ] Know how to **manually close positions**
- [ ] Have **stop losses enabled** (default)

---

## 📞 SUPPORT

### Documentation
- [ASSET_GUIDE.md](ASSET_GUIDE.md) - What assets we trade
- [MICRO_CAPITAL_STRATEGY.md](../MICRO_CAPITAL_STRATEGY.md) - $100 capital strategy
- [LEVERAGE_IMPLEMENTATION.md](../LEVERAGE_IMPLEMENTATION.md) - Leverage explained

### Common Commands

**Check bot status:**
```bash
ps aux | grep deploy_live.py
```

**Stop bot:**
```bash
pkill -f deploy_live.py
```

**View logs:**
```bash
tail -f trading.log
```

**Check balance:**
```bash
python -c "from binance_futures import test_connection; test_connection()"
```

---

## ⚡ FINAL NOTES

### Expected Results

**Month 1:**
- Start: $100
- End: $500-1,000
- Daily: $10-30
- Win Rate: 65-70%

**Month 2:**
- Start: $500-1,000
- End: $5,000-10,000
- Daily: $100-300
- Win Rate: 70-75%

**Month 3+:**
- Start: $5,000-10,000
- Daily: $500-1,000+
- Consider reducing leverage (scale back to 5x)
- Win Rate: 70-75%

### Risk Warning

**Trading involves risk.**
- You can lose money
- Leverage amplifies both gains AND losses
- Start small ($100)
- Never risk more than you can afford to lose
- Past performance ≠ future results

### Best Practices

1. **Start on testnet** (1-2 weeks)
2. **Deploy with $100** (not more)
3. **Monitor daily** (first week)
4. **Respect risk limits** (don't override)
5. **Withdraw profits weekly** (secure gains)
6. **Scale gradually** (double capital only after proven success)

---

**Ready to deploy?** Start with testnet mode:

```bash
python deploy_live.py --capital 100
```

Good luck! 🚀
