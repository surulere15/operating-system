# ⚡ Quick Start - 10 Minutes to Running SaaS

**Get the multi-tenant trading bot SaaS running locally in 10 minutes**

---

## 🎯 Prerequisites

- Python 3.11+ installed
- Node.js 18+ installed
- PostgreSQL 15+ installed

---

## 📦 Step 1: Clone & Setup (2 min)

```bash
cd /Users/sam/.openclaw/workspace/trading-bot-saas
```

---

## 🗄️ Step 2: Database (2 min)

```bash
# Create database
createdb trading_bot_saas

# Verify
psql trading_bot_saas -c "SELECT 1;"
```

**Expected:** `?column? | 1`

---

## 🔧 Step 3: Backend (3 min)

```bash
cd backend

# Install
pip3 install -r requirements.txt

# Configure
cat > .env << EOF2
DATABASE_URL=postgresql://$(whoami)@localhost/trading_bot_saas
JWT_SECRET=$(openssl rand -hex 32)
ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
STRIPE_SECRET_KEY=sk_test_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx
EOF2

# Initialize database
python3 -c "from database import init_db; init_db()"

# Start backend
uvicorn main:app --reload &
```

**Expected:**
```
✅ Database tables created
✅ Trading Bot SaaS API running
INFO:     Uvicorn running on http://127.0.0.1:8000
```

---

## 🎨 Step 4: Frontend (3 min)

```bash
cd ../frontend

# Install
npm install

# Configure
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Start
npm run dev
```

**Expected:**
```
✓ Ready in 2.5s
○ Local: http://localhost:3000
```

---

## ✅ Step 5: Test (1 min)

1. **Open:** http://localhost:3000
2. **Register:** Create account with email/password
3. **Dashboard:** You should see empty dashboard
4. **Create Bot:** Click "Create Bot" button

---

## 🎯 What You Built

### ✅ Backend Features
- User authentication (JWT)
- Encrypted API key storage
- Bot management endpoints
- Trade tracking
- Stripe webhooks

### ✅ Frontend Features
- Login/Register UI
- Trading dashboard
- Bot management cards
- Real-time stats
- Responsive design

---

## 🔍 Verify Everything Works

### Test Backend API
```bash
curl http://localhost:8000
# Should return: {"status":"online","service":"Trading Bot SaaS API"}
```

### Test User Registration
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123","full_name":"Test User"}'

# Should return: {"token":"eyJ...","user":{...}}
```

### Test Database
```bash
psql trading_bot_saas -c "SELECT email, tier FROM users;"

# Should show your registered user
```

---

## 🚀 Next Steps

### Week 2 Tasks:
1. **Stripe Integration:** Add checkout flow
2. **Bot Engine:** Connect to trading bot
3. **Real-time Updates:** WebSocket for live trades
4. **Charts:** Add Recharts for PnL visualization

### Week 3 Tasks:
1. **Polish UI:** Mobile responsive
2. **Email Notifications:** Trade alerts
3. **Documentation:** User guides
4. **Deploy:** Vercel + Railway

---

## 🛟 Troubleshooting

### Backend won't start
```bash
# Check PostgreSQL
psql trading_bot_saas -c "SELECT 1;"

# Check dependencies
pip3 install -r requirements.txt
```

### Frontend won't start
```bash
# Check Node version (need 18+)
node --version

# Clean install
rm -rf node_modules package-lock.json
npm install
```

### Database errors
```bash
# Drop and recreate
dropdb trading_bot_saas
createdb trading_bot_saas

# Reinitialize
cd backend
python3 -c "from database import init_db; init_db()"
```

---

## 📊 URLs

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend** | http://localhost:3000 | User dashboard |
| **Backend** | http://localhost:8000 | API endpoints |
| **Docs** | http://localhost:8000/docs | Swagger API docs |
| **Database** | localhost:5432 | PostgreSQL |

---

## 🎯 You're Live!

**What you have:**
- ✅ Multi-tenant SaaS platform
- ✅ User authentication system
- ✅ Encrypted API key storage
- ✅ Bot management dashboard
- ✅ Database with proper schema
- ✅ Stripe integration (ready)

**What's next:**
- Connect real trading bot engine
- Add payment checkout
- Deploy to production

---

## 💰 Revenue Potential

**With 100 users:**
- 50 × $29 (Starter) = $1,450
- 30 × $79 (Pro) = $2,370
- 20 × $199 (Elite) = $3,980
- **Total MRR:** $7,800/month

**Week 1 investment:** $1,000
**Month 1 ROI:** 780%

---

**You're ready to build a profitable SaaS! 🚀**

Check [README.md](README.md) for full documentation.
