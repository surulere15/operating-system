# Integration Guide - Adding Infrastructure to Main App

## Quick Start

### 1. Update main.py startup

Add infrastructure initialization to your FastAPI app:

```python
from fastapi import FastAPI, Depends
from infrastructure_integration import (
    initialize_infrastructure,
    get_infra_dependency,
    InfrastructureConfig
)

# Create app
app = FastAPI(title="Trading Bot SaaS")

# Initialize infrastructure on startup
@app.on_event("startup")
async def startup():
    """Initialize infrastructure"""
    config = InfrastructureConfig()
    infra = initialize_infrastructure(config)

    # Create database tables if they don't exist
    infra.database.create_all_tables()

    print("✅ Application started with production infrastructure")

@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown"""
    print("👋 Application shutting down")
```

### 2. Add Health Check Endpoint

```python
@app.get("/api/health")
async def health_check(infra = Depends(get_infra_dependency)):
    """System health check"""
    return await infra.get_health_status()

@app.get("/api/metrics")
async def get_metrics(infra = Depends(get_infra_dependency)):
    """System metrics"""
    return infra.get_system_metrics()
```

### 3. Update Database Operations

**Before (old database.py):**
```python
from database import get_db, User, Bot

@app.get("/api/bots")
def get_bots(db: Session = Depends(get_db)):
    bots = db.query(Bot).all()
    return bots
```

**After (new database_operations.py):**
```python
@app.get("/api/bots")
async def get_bots(infra = Depends(get_infra_dependency)):
    async with infra.get_repository_context() as repo:
        bots = repo.bots.get_active_bots()
        return bots
```

### 4. Add Production Safeguards to Trading Operations

**Before:**
```python
@app.post("/api/trades")
async def create_trade(trade_data: dict):
    # Direct exchange call - no error handling
    order = exchange.create_order(...)
    return order
```

**After:**
```python
@app.post("/api/trades")
async def create_trade(trade_data: dict, infra = Depends(get_infra_dependency)):
    try:
        # Execute with production safeguards
        async def place_order():
            # Check rate limit before making exchange call
            if not await infra.production.rate_limiter.acquire("exchange_api"):
                await infra.production.rate_limiter.wait_if_needed()

            # Make exchange call through circuit breaker
            order = await exchange.create_order(...)
            return order

        # Execute with retry and circuit breaker
        order = await infra.production.execute_safe(place_order)

        # Store in database
        async with infra.get_repository_context() as repo:
            trade = repo.trades.create_trade(
                bot_id=trade_data['bot_id'],
                user_id=trade_data['user_id'],
                symbol=trade_data['symbol'],
                side=trade_data['side'],
                action=TradeAction.ENTER,
                order_type="market",
                price=order['price'],
                size=order['amount'],
                cost=order['cost'],
                exchange="binance",
                order_id=order['id']
            )

        # Record metrics
        infra.monitoring.metrics.increment_counter(
            "trades_executed",
            labels={"status": "success", "symbol": trade_data['symbol']}
        )

        return trade

    except Exception as e:
        # Capture exception in Sentry
        infra.monitoring.error_tracker.capture_exception(
            e,
            context={"trade_data": trade_data}
        )

        # Record metric
        infra.monitoring.metrics.increment_counter(
            "trades_failed",
            labels={"symbol": trade_data['symbol']}
        )

        raise HTTPException(status_code=500, detail=str(e))
```

### 5. Update Bot Management

```python
@app.post("/api/bots")
async def create_bot(bot_data: dict, infra = Depends(get_infra_dependency)):
    """Create new trading bot"""
    async with infra.get_repository_context() as repo:
        # Create bot
        bot = repo.bots.create_bot(
            user_id=bot_data['user_id'],
            name=bot_data['name'],
            exchange=bot_data['exchange'],
            symbols=bot_data['symbols'],
            parameters=bot_data['parameters'],
            allocated_capital=bot_data['capital']
        )

        # Record metric
        infra.monitoring.metrics.increment_counter("bots_created")

        return bot

@app.post("/api/bots/{bot_id}/start")
async def start_bot(bot_id: int, infra = Depends(get_infra_dependency)):
    """Start trading bot"""
    async with infra.get_repository_context() as repo:
        # Update bot status
        repo.bots.update_bot_status(bot_id, BotStatus.ACTIVE)

        # Record event
        repo.events.log_event(
            event_type="bot_started",
            severity="info",
            message=f"Bot {bot_id} started",
            bot_id=bot_id
        )

    return {"status": "started"}
```

### 6. Secure API Key Storage

**Before:**
```python
@app.post("/api/exchange-keys")
def store_keys(keys: dict):
    # Store plaintext keys - INSECURE!
    db.save(api_key=keys['api_key'])
```

**After:**
```python
@app.post("/api/exchange-keys")
async def store_keys(keys: dict, infra = Depends(get_infra_dependency)):
    """Store exchange API keys securely"""

    # Encrypt and store in key vault
    infra.production.key_vault.store_api_key(
        key_id=f"user_{keys['user_id']}_binance",
        api_key=keys['api_key'],
        api_secret=keys['api_secret'],
        passphrase=keys.get('passphrase')
    )

    # Store reference in database
    async with infra.get_repository_context() as repo:
        cred = repo.credentials.store_credentials(
            user_id=keys['user_id'],
            exchange_name="binance",
            encrypted_api_key=f"vault:user_{keys['user_id']}_binance",
            encrypted_api_secret="stored_in_vault",
            is_testnet=keys.get('is_testnet', False)
        )

    return {"status": "stored_securely"}

@app.get("/api/exchange-keys/{user_id}")
async def get_keys(user_id: int, infra = Depends(get_infra_dependency)):
    """Retrieve exchange API keys"""

    # Retrieve from key vault
    credentials = infra.production.key_vault.retrieve_api_key(
        f"user_{user_id}_binance"
    )

    if credentials:
        return {
            "exchange": "binance",
            "api_key": credentials['api_key'][:10] + "...",  # Masked
            "has_secret": True
        }

    raise HTTPException(status_code=404, detail="Keys not found")
```

### 7. Add Performance Profiling

```python
@app.post("/api/signals/generate")
async def generate_signals(infra = Depends(get_infra_dependency)):
    """Generate trading signals with performance profiling"""

    # Profile the operation
    with infra.monitoring.profiler.profile("signal_generation"):
        # Generate signals
        signals = await signal_generator.generate_signals()

    # Store signals in database
    async with infra.get_repository_context() as repo:
        for signal_data in signals:
            signal = repo.signals.create_signal(
                bot_id=signal_data['bot_id'],
                symbol=signal_data['symbol'],
                signal_type=signal_data['type'],
                price=signal_data['price'],
                confidence_score=signal_data['confidence'],
                ml_score=signal_data['ml_score'],
                sentiment_score=signal_data['sentiment_score']
            )

    # Record metric
    infra.monitoring.metrics.increment_counter(
        "signals_generated",
        value=len(signals)
    )

    return signals
```

### 8. Monitor Position Tracking

```python
@app.post("/api/positions/open")
async def open_position(position_data: dict, infra = Depends(get_infra_dependency)):
    """Open new position with capital tracking"""

    bot_id = position_data['bot_id']
    required_capital = position_data['size'] * position_data['entry_price']

    # Check if can open position
    if not await infra.production.position_tracker.can_open_position(bot_id, required_capital):
        raise HTTPException(
            status_code=400,
            detail="Insufficient capital or too many open positions"
        )

    # Create position object
    from production_infrastructure import Position, PositionStatus

    position = Position(
        position_id=f"pos_{position_data['id']}",
        bot_id=bot_id,
        symbol=position_data['symbol'],
        side=position_data['side'],
        entry_price=position_data['entry_price'],
        size=position_data['size'],
        status=PositionStatus.OPEN
    )

    # Track position
    success = await infra.production.position_tracker.open_position(position)

    if success:
        # Store in database
        async with infra.get_repository_context() as repo:
            db_position = repo.positions.open_position(
                bot_id=bot_id,
                user_id=position_data['user_id'],
                symbol=position_data['symbol'],
                side=position_data['side'],
                entry_price=position_data['entry_price'],
                size=position_data['size'],
                entry_capital=required_capital
            )

        # Record metric
        infra.monitoring.metrics.set_gauge(
            "open_positions",
            len(infra.production.position_tracker.positions)
        )

        return db_position

    raise HTTPException(status_code=500, detail="Failed to open position")
```

### 9. Error Tracking Example

```python
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler with Sentry integration"""

    infra = get_infrastructure()

    # Capture in Sentry
    infra.monitoring.error_tracker.capture_exception(
        exc,
        context={
            "path": request.url.path,
            "method": request.method,
            "headers": dict(request.headers)
        }
    )

    # Create alert
    infra.monitoring.alert_manager.create_alert(
        AlertSeverity.ERROR,
        "Unhandled Exception",
        str(exc),
        "api",
        {"path": request.url.path}
    )

    # Record metric
    infra.monitoring.metrics.increment_counter(
        "unhandled_exceptions",
        labels={"path": request.url.path}
    )

    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )
```

### 10. Environment Configuration

Create `.env` file:

```bash
# Database
DATABASE_URL=postgresql://trading_user:password@localhost/trading_bot
DATABASE_ECHO=false

# Monitoring
SENTRY_DSN=https://your-sentry-dsn@sentry.io/123456
ENVIRONMENT=production

# Rate Limiting
RATE_LIMIT_PER_SECOND=10
RATE_LIMIT_PER_MINUTE=100
RATE_LIMIT_PER_HOUR=1000
RATE_LIMIT_PER_DAY=10000

# Circuit Breaker
CIRCUIT_BREAKER_FAILURE_THRESHOLD=5
CIRCUIT_BREAKER_RECOVERY_TIMEOUT=60

# Security
ENCRYPTION_KEY=your-32-byte-fernet-key-here

# Retry Config
MAX_RETRY_ATTEMPTS=3
RETRY_BASE_DELAY=1.0
RETRY_MAX_DELAY=60.0
```

Load in main.py:

```python
from dotenv import load_dotenv
load_dotenv()
```

---

## Complete Example: Updated Endpoint

Here's a complete example showing before and after:

### Before (No Infrastructure)

```python
@app.post("/api/bot/{bot_id}/trade")
def execute_trade(bot_id: int, signal: dict):
    # Get bot
    bot = db.query(Bot).filter(Bot.id == bot_id).first()

    # Make exchange call (no error handling, rate limiting, or retry)
    order = exchange.create_order(
        symbol=signal['symbol'],
        type='market',
        side=signal['side'],
        amount=signal['size']
    )

    # Store trade (no transaction management)
    trade = Trade(
        bot_id=bot_id,
        symbol=signal['symbol'],
        side=signal['side'],
        price=order['price'],
        size=order['amount']
    )
    db.add(trade)
    db.commit()

    return order
```

### After (With Full Infrastructure)

```python
@app.post("/api/bot/{bot_id}/trade")
async def execute_trade(
    bot_id: int,
    signal: dict,
    infra = Depends(get_infra_dependency)
):
    """
    Execute trade with full production infrastructure:
    - Error handling with retry
    - Rate limiting
    - Circuit breaker
    - Database transactions
    - Monitoring and metrics
    - Error tracking
    - Performance profiling
    """

    # Profile the operation
    with infra.monitoring.profiler.profile("trade_execution"):
        try:
            # Define trade execution function
            async def place_order():
                # Check rate limit
                if not await infra.production.rate_limiter.acquire("exchange_api"):
                    await infra.production.rate_limiter.wait_if_needed()

                # Make exchange call
                order = await exchange.create_order(
                    symbol=signal['symbol'],
                    type='market',
                    side=signal['side'],
                    amount=signal['size']
                )
                return order

            # Execute with production safeguards (retry + circuit breaker)
            order = await infra.production.execute_safe(place_order)

            # Store in database with transaction management
            async with infra.get_repository_context() as repo:
                # Get bot
                bot = repo.bots.get_bot_by_id(bot_id)

                # Create trade
                trade = repo.trades.create_trade(
                    bot_id=bot_id,
                    user_id=bot.user_id,
                    symbol=signal['symbol'],
                    side=signal['side'],
                    action=TradeAction.ENTER,
                    order_type='market',
                    price=order['price'],
                    size=order['amount'],
                    cost=order['cost'],
                    exchange='binance',
                    order_id=order['id'],
                    status=OrderStatus.FILLED
                )

                # Update bot performance
                repo.bots.update_bot_performance(bot_id, {
                    'pnl': order.get('pnl', 0)
                })

            # Record success metrics
            infra.monitoring.metrics.increment_counter(
                "trades_executed",
                labels={
                    "status": "success",
                    "symbol": signal['symbol'],
                    "side": signal['side']
                }
            )

            # Record latency
            infra.monitoring.metrics.observe_histogram(
                "trade_execution_latency_ms",
                order.get('latency_ms', 0),
                labels={"symbol": signal['symbol']}
            )

            return {
                "success": True,
                "trade_id": trade.id,
                "order": order
            }

        except Exception as e:
            # Capture exception in Sentry
            infra.monitoring.error_tracker.capture_exception(
                e,
                context={
                    "bot_id": bot_id,
                    "signal": signal,
                    "operation": "trade_execution"
                }
            )

            # Create alert
            infra.monitoring.alert_manager.create_alert(
                AlertSeverity.ERROR,
                "Trade Execution Failed",
                f"Failed to execute trade for bot {bot_id}: {str(e)}",
                "trading",
                {"bot_id": bot_id, "symbol": signal['symbol']}
            )

            # Record failure metric
            infra.monitoring.metrics.increment_counter(
                "trades_failed",
                labels={"symbol": signal['symbol'], "error": type(e).__name__}
            )

            raise HTTPException(
                status_code=500,
                detail=f"Trade execution failed: {str(e)}"
            )
```

---

## Migration Checklist

- [ ] Install new dependencies (if any)
- [ ] Set up environment variables
- [ ] Initialize infrastructure on app startup
- [ ] Add health check endpoint
- [ ] Update database operations to use repositories
- [ ] Add production safeguards to exchange calls
- [ ] Implement error tracking
- [ ] Add metrics collection
- [ ] Update API key storage to use encryption
- [ ] Implement position tracking
- [ ] Add performance profiling
- [ ] Test health checks
- [ ] Test error handling and retry
- [ ] Verify rate limiting works
- [ ] Check Sentry integration
- [ ] Review all metrics

---

## Testing

```python
# Test health check
curl http://localhost:8000/api/health

# Test metrics
curl http://localhost:8000/api/metrics

# Test with failure (should retry)
# Temporarily break exchange connection and verify retry works

# Test rate limiting
# Make rapid requests and verify rate limiting activates

# Test circuit breaker
# Cause multiple failures and verify circuit opens
```

---

## Summary

Key changes needed:

1. **Startup:** Initialize infrastructure
2. **Dependencies:** Use `get_infra_dependency()`
3. **Database:** Use repository pattern
4. **Trading:** Add safeguards (retry, rate limit, circuit breaker)
5. **Monitoring:** Record metrics and errors
6. **Security:** Encrypt API keys
7. **Health:** Add health/metrics endpoints

**Result:** Production-ready platform with enterprise-grade reliability and observability.
