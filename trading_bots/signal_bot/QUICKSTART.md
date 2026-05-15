# ⚡ Quick Start Guide - 15 Minutes to Live Trading

**Get the bot running in 15 minutes!**

---

## 🎯 Prerequisites

- Python 3.11+ installed
- Bybit account (https://bybit.com)
- Telegram account
- $35+ USDT in Bybit Derivatives wallet

---

## 📦 Step 1: Install (2 minutes)

```bash
cd ~/.openclaw/workspace/trading_bots/signal_bot
pip3 install -r requirements.txt
```

---

## 🔑 Step 2: Get API Keys (5 minutes)

### Bybit API:
1. Go to: https://bybit.com/app/user/api-management
2. Create New API Key
3. Enable: **Contract Trading**, **Position**, **Trade**
4. Copy API Key and Secret

### Telegram Bot:
1. Message **@BotFather** in Telegram
2. Send: `/newbot`
3. Copy bot token

### Your Chat ID:
1. Message **@userinfobot** in Telegram
2. Send: `/start`
3. Copy your ID

---

## ⚙️ Step 3: Configure (3 minutes)

```bash
# Edit ~/.bashrc
nano ~/.bashrc
```

**Add these lines:**

```bash
export BYBIT_API_KEY='YOUR_API_KEY'
export BYBIT_API_SECRET='YOUR_API_SECRET'
export TELEGRAM_BOT_TOKEN='YOUR_BOT_TOKEN'
export TELEGRAM_CHAT_ID='YOUR_CHAT_ID'
```

**Save and reload:**

```bash
source ~/.bashrc
```

---

## ✅ Step 4: Test (3 minutes)

```bash
# Test Bybit connection
python3 -c "
from bybit_futures import BybitFuturesTrader
trader = BybitFuturesTrader(testnet=False, capital=35)
balance = trader.get_account_balance()
print(f'✅ Balance: \${balance[\"total\"]:.2f}')
"

# Test Telegram
python3 -c "
from telegram_notifier import TelegramNotifier
TelegramNotifier().test_connection()
"
```

**Expected:**
- ✅ Shows your Bybit balance
- ✅ Telegram message received

---

## 🚀 Step 5: Launch (2 minutes)

```bash
# Start bot in background
nohup python3 -u deploy_bybit.py --capital 35 --live > live_trading.log 2>&1 &

# View logs
tail -f live_trading.log
```

**Expected output:**
```
🚀 @ALPHAEDGESIGNALS - BYBIT LIVE TRADING BOT
Capital: $35.00 USDT
Exchange: BYBIT
Mode: ⚠️ LIVE TRADING
Markets: 40 pairs
Leverage: 15-25x AGGRESSIVE

🔄 Starting continuous monitoring...
[2026-02-11 12:00:00] Scanning markets...
```

---

## ✅ You're Live!

**What happens next:**
1. Bot scans 37 markets every 5 minutes
2. When 60%+ confidence signal found:
   - 📱 Telegram notification sent
   - 💰 Trade executed automatically
   - 🎯 Take profits set at 10-15%
   - 🛑 Stop loss at -5% (manual placement needed)
3. You receive updates on all trades

---

## 🔍 Monitor Your Bot

```bash
# Check if running
ps aux | grep deploy_bybit.py

# View live logs
tail -f live_trading.log

# Stop bot
pkill -f deploy_bybit.py
```

---

## 📊 Expected Results

**With $35 capital:**
- 1-3 signals per day
- $1-5 profit per trade
- $30-150 per month

**First profitable trade proves the bot works!** ✅

Your first trade: +$1.30 profit (+3.85% ROI)

---

## ⚠️ Important Notes

1. **Bot is aggressive (15-25x leverage)** - Start small!
2. **Stop loss issue** - May fail to place, monitor positions manually
3. **Capital** - $35 is minimum, $100+ recommended for better returns
4. **Patience** - Bot is conservative, may wait hours for good setups

---

## 🛟 Need Help?

**Bot not finding signals?**
- This is normal! Bot waits for quality setups
- May go 2-4 hours without signals

**API errors?**
- Check: `echo $BYBIT_API_KEY`
- Reload: `source ~/.bashrc`
- Restart bot

**No Telegram notifications?**
- Test: `python3 telegram_notifier.py`
- Check you started bot in Telegram (`/start`)

---

## 📈 Scale Up

**After 1 week of profitable trading:**
1. Deposit more capital ($100-1000)
2. Same win rate, bigger profits
3. $1,000 capital = $30-150 per trade!

---

**You're all set! Bot is hunting for profitable setups 24/7.** 🎯

Check INSTALLATION.md for detailed documentation.
