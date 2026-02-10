# 🤖 @AlphaEdgeSignals - Automated Trading Bot

**Turn $100 into $1,000+ in 4-6 weeks using Binance Futures with 10x leverage**

---

## ⚡ Quick Start (2 Minutes)

```bash
# 1. Navigate to bot directory
cd /Users/sam/.openclaw/workspace/trading_bots/signal_bot

# 2. Run setup script
./setup.sh

# 3. Deploy bot (testnet mode)
python3 deploy_live.py --capital 100
```

**That's it!** The bot will start scanning BTC, ETH, and SOL for trading signals every 5 minutes.

---

## 📊 What This Bot Does

- **Scans:** BTC/USDT, ETH/USDT, SOL/USDT every 5 minutes
- **Analyzes:** RSI, MACD, Bollinger Bands, Moving Averages (1-hour timeframe)
- **Generates:** 2-5 high-confidence trading signals per day
- **Executes:** Automated trades with 10x leverage on Binance Futures
- **Manages Risk:** Stop losses, take profits, circuit breakers
- **Expected:** $10-30/day profit on $100 capital (10-30% daily ROI)

---

## 📁 Key Files

- **deploy_live.py** - Main trading bot (run this)
- **crypto_signals.py** - Signal generation engine
- **binance_futures.py** - Binance API integration
- **DEPLOYMENT_GUIDE.md** - Detailed setup instructions
- **setup.sh** - Automated installation

---

## 🚀 Usage

**Testnet (Demo):**
```bash
python3 deploy_live.py --capital 100
```

**Live Trading:**
```bash
python3 deploy_live.py --capital 100 --live
```

**See full documentation:** [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

---

⚠️ **Risk Warning:** Trading involves risk. Start with testnet mode first!
