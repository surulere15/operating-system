"""
Core Trading Engine
Handles signal generation, risk management, and trade execution

PROFIT MAXIMIZATION ENHANCEMENTS:
- Accurate PnL with fees, slippage, funding rates
- Limit orders with market fallback (reduce slippage)
- Dynamic position sizing based on confidence
- ATR-based stop loss (volatility-adjusted)
- Strategy-specific take profit targets
"""

import ccxt
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging
import asyncio
from database import get_db, Bot, APIKey, Trade, decrypt_value
from sqlalchemy.orm import Session
from strategies import StrategyFactory
from dynamic_position_sizing import DynamicPositionSizer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TradingEngine:
    """
    Multi-tenant trading engine that executes trades for bots

    Features:
    - Technical analysis signal generation
    - Risk management (position sizing, stop loss, take profit)
    - Multi-exchange support via CCXT
    - Real-time trade execution
    """

    def __init__(self, bot_id: int, db: Session):
        """Initialize trading engine for a specific bot"""
        self.bot_id = bot_id
        self.db = db
        self.bot = db.query(Bot).filter(Bot.id == bot_id).first()

        if not self.bot:
            raise ValueError(f"Bot {bot_id} not found")

        self.user_id = self.bot.user_id
        self.config = self.bot.config or {}
        self.exchange_client = None

        # Initialize trading strategy
        strategy_name = self.config.get('strategy', 'ma_crossover')
        self.strategy = StrategyFactory.create_strategy(strategy_name, self.config)
        logger.info(f"📊 Using strategy: {strategy_name}")

        # Initialize profit maximization components
        self.position_sizer = DynamicPositionSizer(
            base_risk_per_trade=0.02,  # 2% risk per trade
            max_position_size=0.12      # 12% max size
        )
        self.peak_prices = {}  # For trailing stops: trade_id -> peak price

        # Exchange fee structure (Binance futures default)
        self.fees = {
            'maker': 0.0002,  # 0.02%
            'taker': 0.0004,  # 0.04%
            'funding_rate_avg': 0.0001  # 0.01% per 8h
        }

        # Initialize exchange connection
        self._init_exchange()

    def _init_exchange(self):
        """Initialize CCXT exchange connection"""
        try:
            # Get user's API keys for this exchange
            api_key_obj = self.db.query(APIKey).filter(
                APIKey.user_id == self.user_id,
                APIKey.exchange == self.bot.exchange,
                APIKey.is_active == True
            ).first()

            if not api_key_obj:
                raise ValueError(f"No API key found for {self.bot.exchange}")

            # Decrypt API credentials
            api_key = decrypt_value(api_key_obj.api_key)
            api_secret = decrypt_value(api_key_obj.api_secret)

            # Initialize CCXT exchange
            exchange_class = getattr(ccxt, self.bot.exchange.lower())
            self.exchange_client = exchange_class({
                'apiKey': api_key,
                'secret': api_secret,
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'future',  # Use futures by default
                }
            })

            # Set testnet if configured
            if api_key_obj.is_testnet:
                self.exchange_client.set_sandbox_mode(True)

            logger.info(f"✅ Initialized {self.bot.exchange} exchange for bot {self.bot_id}")

        except Exception as e:
            logger.error(f"❌ Failed to initialize exchange for bot {self.bot_id}: {str(e)}")
            raise

    def generate_signal(self, symbol: str) -> Dict:
        """
        Generate trading signal using configured strategy

        Returns: {'action': 'buy'|'sell'|'hold', 'confidence': 0-100, 'reason': str}
        """
        try:
            # Fetch OHLCV data (15-minute candles, last 100 bars)
            timeframe = self.config.get('timeframe', '15m')
            ohlcv = self.exchange_client.fetch_ohlcv(symbol, timeframe=timeframe, limit=100)

            if len(ohlcv) < 20:
                return {'action': 'hold', 'confidence': 0, 'reason': 'Insufficient data'}

            # Get current price
            current_price = ohlcv[-1][4]  # Close price

            # Delegate to strategy
            signal = self.strategy.generate_signal(ohlcv, current_price)

            logger.info(f"📊 Signal for {symbol}: {signal}")
            return signal

        except Exception as e:
            logger.error(f"❌ Signal generation failed for {symbol}: {str(e)}")
            return {'action': 'hold', 'confidence': 0, 'reason': f'Error: {str(e)}'}

    def check_risk_limits(self) -> Tuple[bool, str]:
        """
        Check if bot is within risk limits
        Returns: (can_trade: bool, reason: str)
        """
        try:
            # Get today's trades
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            today_trades = self.db.query(Trade).filter(
                Trade.bot_id == self.bot_id,
                Trade.opened_at >= today_start,
                Trade.status == 'closed'
            ).all()

            # Calculate today's P&L
            today_pnl = sum(t.pnl or 0 for t in today_trades)
            today_pnl_percent = (today_pnl / self.bot.capital) * 100 if self.bot.capital > 0 else 0

            # Check max daily loss
            max_daily_loss = self.config.get('max_daily_loss', 10)
            if today_pnl_percent <= -max_daily_loss:
                return False, f"Daily loss limit reached ({today_pnl_percent:.2f}% / -{max_daily_loss}%)"

            # Check if bot has enough capital
            if self.bot.current_balance < 10:  # Minimum $10
                return False, "Insufficient balance (< $10)"

            # Check open positions limit (max 3 concurrent - optimized for 12% position sizing)
            open_positions = self.db.query(Trade).filter(
                Trade.bot_id == self.bot_id,
                Trade.status == 'open'
            ).count()

            if open_positions >= 3:
                return False, "Maximum open positions reached (3)"

            return True, "All risk checks passed"

        except Exception as e:
            logger.error(f"❌ Risk check failed: {str(e)}")
            return False, f"Risk check error: {str(e)}"

    def _calculate_atr(self, ohlcv: List, period: int = 14) -> float:
        """
        Calculate Average True Range for volatility-adjusted stops

        Args:
            ohlcv: OHLCV candles
            period: ATR period

        Returns:
            Current ATR value
        """
        if len(ohlcv) < period + 1:
            return 0

        true_ranges = []
        for i in range(1, len(ohlcv)):
            high = ohlcv[i][2]
            low = ohlcv[i][3]
            prev_close = ohlcv[i-1][4]

            tr = max(
                high - low,
                abs(high - prev_close),
                abs(low - prev_close)
            )
            true_ranges.append(tr)

        atr = np.mean(true_ranges[-period:])
        return atr

    def _get_market_volatility(self, symbol: str) -> float:
        """Get current market volatility as % of price"""
        try:
            ohlcv = self.exchange_client.fetch_ohlcv(symbol, timeframe='15m', limit=50)
            if len(ohlcv) < 20:
                return 0.02  # Default 2% volatility

            current_price = ohlcv[-1][4]
            atr = self._calculate_atr(ohlcv)
            volatility_pct = atr / current_price

            return volatility_pct

        except Exception as e:
            logger.warning(f"⚠️ Could not get volatility: {str(e)}")
            return 0.02  # Default

    def calculate_position_size(self, symbol: str, leverage: int, signal_confidence: int = 70) -> float:
        """
        Calculate position size with DYNAMIC SIZING based on signal confidence
        Uses optimized 12% base with adjustments for confidence, drawdown, volatility

        Args:
            symbol: Trading pair
            leverage: Leverage multiplier
            signal_confidence: Signal confidence (0-100)

        Returns:
            Position quantity
        """
        try:
            # Get current market price
            ticker = self.exchange_client.fetch_ticker(symbol)
            current_price = ticker['last']

            # Get market volatility
            volatility = self._get_market_volatility(symbol)

            # Calculate dynamic position size
            decision = self.position_sizer.calculate_position_size(
                symbol=symbol,
                signal_confidence=signal_confidence / 100.0,  # Convert to 0-1
                expected_return=0.015,  # 1.5% expected return
                market_volatility=volatility,
                stop_loss_pct=0.025  # 2.5% stop
            )

            # Use dynamic size (already accounts for confidence, drawdown, volatility)
            capital_per_trade = self.bot.current_balance * decision.final_size

            logger.info(f"💰 Dynamic sizing: {decision.final_size*100:.1f}% of capital (confidence: {signal_confidence}%)")
            logger.info(f"   Base: {decision.base_size*100:.1f}% → Final: {decision.final_size*100:.1f}% (multiplier: {decision.calculate_total_multiplier():.2f}x)")

            # Calculate quantity with leverage
            position_value = capital_per_trade * leverage
            quantity = position_value / current_price

            # Round to exchange precision
            market = self.exchange_client.market(symbol)
            precision = market.get('precision', {}).get('amount', 3)
            quantity = round(quantity, precision)

            logger.info(f"💰 Position size for {symbol}: {quantity} (${position_value:.2f} value)")
            return quantity

        except Exception as e:
            logger.error(f"❌ Position size calculation failed: {str(e)}")
            # Fallback to simple 12% calculation
            try:
                capital_per_trade = self.bot.current_balance * 0.12
                ticker = self.exchange_client.fetch_ticker(symbol)
                current_price = ticker['last']
                quantity = (capital_per_trade * leverage) / current_price
                return round(quantity, 3)
            except:
                return 0

    def execute_trade(self, symbol: str, action: str, confidence: int) -> Optional[Trade]:
        """
        Execute a trade on the exchange
        Returns: Trade object if successful, None otherwise
        """
        try:
            # Check confidence threshold
            min_confidence = self.config.get('confidence_threshold', 60)
            if confidence < min_confidence:
                logger.info(f"⏸️ Signal confidence ({confidence}%) below threshold ({min_confidence}%)")
                return None

            # Check risk limits
            can_trade, reason = self.check_risk_limits()
            if not can_trade:
                logger.warning(f"⚠️ Cannot trade: {reason}")
                return None

            # Get leverage for this market
            leverage_config = self.config.get('leverage', {})
            leverage = leverage_config.get(symbol, 15)  # Default 15x

            # Fetch market data for calculations
            ohlcv = self.exchange_client.fetch_ohlcv(symbol, timeframe='15m', limit=50)
            ticker = self.exchange_client.fetch_ticker(symbol)
            current_price = ticker['last']
            bid = ticker.get('bid', current_price)
            ask = ticker.get('ask', current_price)

            # Calculate position size with DYNAMIC SIZING (uses confidence)
            quantity = self.calculate_position_size(symbol, leverage, confidence)
            if quantity <= 0:
                logger.warning(f"⚠️ Invalid position size: {quantity}")
                return None

            # Set leverage on exchange
            try:
                self.exchange_client.set_leverage(leverage, symbol)
            except Exception as e:
                logger.warning(f"⚠️ Could not set leverage: {str(e)} (may not be supported)")

            # Calculate ATR-based stop loss (volatility-adjusted)
            atr = self._calculate_atr(ohlcv)
            atr_pct = atr / current_price
            stop_loss_pct = max(min(atr_pct * 2.0, 0.05), 0.015)  # 2x ATR, max 5%, min 1.5%

            # Strategy-specific take profit
            strategy_name = self.config.get('strategy', 'ma_crossover')
            if strategy_name in ['stat_arb', 'mean_reversion', 'pair_trading']:
                take_profit_pct = 0.015  # 1.5% for mean reversion
            elif strategy_name in ['trend_following', 'breakout']:
                take_profit_pct = 0.05   # 5% for trend
            else:
                # Dynamic based on volatility
                take_profit_pct = min(atr_pct * 2.5, 0.05)  # 2.5x ATR, max 5%

            logger.info(f"📊 ATR: {atr:.2f} ({atr_pct*100:.2f}%) | Stop: {stop_loss_pct*100:.1f}% | TP: {take_profit_pct*100:.1f}%")

            # Calculate stop and target prices
            if action == 'buy':
                stop_loss = current_price * (1 - stop_loss_pct)
                take_profit = current_price * (1 + take_profit_pct)
                limit_price = bid + ((ask - bid) * 0.3)  # 30% into spread
            else:  # sell
                stop_loss = current_price * (1 + stop_loss_pct)
                take_profit = current_price * (1 - take_profit_pct)
                limit_price = ask - ((ask - bid) * 0.3)

            # Try LIMIT ORDER first (reduce slippage)
            try:
                logger.info(f"📝 Placing limit order @ ${limit_price:.2f} (spread: {((ask-bid)/bid)*100:.3f}%)")
                order = self.exchange_client.create_order(
                    symbol=symbol,
                    type='limit',
                    side=action,
                    amount=quantity,
                    price=limit_price,
                    params={
                        'timeInForce': 'GTX',  # Post-only
                        'stopLoss': {'triggerPrice': stop_loss},
                        'takeProfit': {'triggerPrice': take_profit}
                    }
                )

                # Wait 30 seconds for fill
                order_id = order['id']
                import time
                for _ in range(6):  # Check 6 times over 30 seconds
                    time.sleep(5)
                    order_status = self.exchange_client.fetch_order(order_id, symbol)
                    if order_status['status'] == 'filled':
                        logger.info(f"✅ Limit order filled @ ${order_status['average']:.2f}")
                        order = order_status
                        break
                else:
                    # Not filled - cancel and use market
                    logger.warning(f"⏰ Limit order not filled in 30s, using market fallback")
                    self.exchange_client.cancel_order(order_id, symbol)
                    raise Exception("Limit order timeout")

            except Exception as e:
                # Fallback to market order
                logger.info(f"🔄 Using market order (reason: {str(e)[:50]})")
                order = self.exchange_client.create_order(
                    symbol=symbol,
                    type='market',
                    side=action,
                    amount=quantity,
                    params={
                        'stopLoss': {'triggerPrice': stop_loss},
                        'takeProfit': {'triggerPrice': take_profit}
                    }
                )

            # Create trade record in database
            trade = Trade(
                bot_id=self.bot_id,
                symbol=symbol,
                side=action,
                entry_price=current_price,
                quantity=quantity,
                leverage=leverage,
                stop_loss=stop_loss,
                take_profit=take_profit,
                status='open',
                exchange_order_id=order.get('id'),
                opened_at=datetime.utcnow()
            )

            self.db.add(trade)
            self.db.commit()
            self.db.refresh(trade)

            logger.info(f"✅ Trade executed: {action.upper()} {quantity} {symbol} @ ${current_price:.2f}")
            return trade

        except Exception as e:
            logger.error(f"❌ Trade execution failed: {str(e)}")
            self.db.rollback()
            return None

    def check_open_positions(self):
        """
        Check and update open positions
        Close positions that hit stop loss, take profit, OR TRAILING STOP
        """
        try:
            open_trades = self.db.query(Trade).filter(
                Trade.bot_id == self.bot_id,
                Trade.status == 'open'
            ).all()

            for trade in open_trades:
                try:
                    # Get current market price
                    ticker = self.exchange_client.fetch_ticker(trade.symbol)
                    current_price = ticker['last']

                    should_close = False
                    close_reason = None

                    # Initialize peak price tracking
                    if trade.id not in self.peak_prices:
                        self.peak_prices[trade.id] = trade.entry_price

                    # Update peak price
                    if trade.side == 'buy':
                        self.peak_prices[trade.id] = max(self.peak_prices[trade.id], current_price)
                    else:
                        self.peak_prices[trade.id] = min(self.peak_prices[trade.id], current_price)

                    # Calculate peak gain
                    if trade.side == 'buy':
                        peak_gain_pct = ((self.peak_prices[trade.id] - trade.entry_price) / trade.entry_price) * 100
                    else:
                        peak_gain_pct = ((trade.entry_price - self.peak_prices[trade.id]) / trade.entry_price) * 100

                    # Check TRAILING STOP (lock in 70% of peak gain if >1%)
                    if peak_gain_pct > 1.0:
                        if trade.side == 'buy':
                            peak_gain_dollars = self.peak_prices[trade.id] - trade.entry_price
                            trailing_stop_price = trade.entry_price + (peak_gain_dollars * 0.70)

                            if current_price < trailing_stop_price:
                                should_close = True
                                close_reason = f'trailing_stop (locking {peak_gain_pct*0.7:.1f}% profit)'
                                logger.info(f"🔒 Trailing stop triggered for trade {trade.id}: Peak ${self.peak_prices[trade.id]:.2f} → Now ${current_price:.2f}")

                        else:  # sell
                            peak_gain_dollars = trade.entry_price - self.peak_prices[trade.id]
                            trailing_stop_price = trade.entry_price - (peak_gain_dollars * 0.70)

                            if current_price > trailing_stop_price:
                                should_close = True
                                close_reason = f'trailing_stop (locking {peak_gain_pct*0.7:.1f}% profit)'
                                logger.info(f"🔒 Trailing stop triggered for trade {trade.id}: Peak ${self.peak_prices[trade.id]:.2f} → Now ${current_price:.2f}")

                    # Check stop loss
                    if not should_close:
                        if trade.side == 'buy' and current_price <= trade.stop_loss:
                            should_close = True
                            close_reason = 'stop_loss'
                        elif trade.side == 'sell' and current_price >= trade.stop_loss:
                            should_close = True
                            close_reason = 'stop_loss'

                    # Check take profit
                    if not should_close:
                        if trade.side == 'buy' and current_price >= trade.take_profit:
                            should_close = True
                            close_reason = 'take_profit'
                        elif trade.side == 'sell' and current_price <= trade.take_profit:
                            should_close = True
                            close_reason = 'take_profit'

                    if should_close:
                        self.close_position(trade, current_price, close_reason)

                except Exception as e:
                    logger.error(f"❌ Error checking position {trade.id}: {str(e)}")
                    continue

        except Exception as e:
            logger.error(f"❌ Error checking open positions: {str(e)}")

    def close_position(self, trade: Trade, exit_price: float, reason: str):
        """Close a trade position with ACCURATE PnL (fees, slippage, funding)"""
        try:
            # Place closing order (try limit first for exits too)
            closing_side = 'sell' if trade.side == 'buy' else 'buy'

            try:
                # Try limit order for exit
                ticker = self.exchange_client.fetch_ticker(trade.symbol)
                bid = ticker.get('bid', exit_price)
                ask = ticker.get('ask', exit_price)

                if closing_side == 'buy':
                    limit_price = bid + ((ask - bid) * 0.3)
                else:
                    limit_price = ask - ((ask - bid) * 0.3)

                order = self.exchange_client.create_order(
                    symbol=trade.symbol,
                    type='limit',
                    side=closing_side,
                    amount=trade.quantity,
                    price=limit_price
                )

                # Wait 15 seconds (faster for exits)
                order_id = order['id']
                import time
                for _ in range(3):
                    time.sleep(5)
                    order_status = self.exchange_client.fetch_order(order_id, trade.symbol)
                    if order_status['status'] == 'filled':
                        order = order_status
                        exit_price = order['average']  # Actual fill price
                        break
                else:
                    self.exchange_client.cancel_order(order_id, trade.symbol)
                    raise Exception("Exit limit timeout")

            except:
                # Fallback to market for exits
                order = self.exchange_client.create_order(
                    symbol=trade.symbol,
                    type='market',
                    side=closing_side,
                    amount=trade.quantity
                )
                exit_price = order.get('average', exit_price)

            # Calculate GROSS P&L (before costs)
            if trade.side == 'buy':
                gross_pnl = (exit_price - trade.entry_price) * trade.quantity * trade.leverage
            else:  # sell
                gross_pnl = (trade.entry_price - exit_price) * trade.quantity * trade.leverage

            # Calculate ALL COSTS (NO MORE PHANTOM PROFITS)
            position_value = trade.entry_price * trade.quantity

            # 1. Trading fees (entry + exit)
            entry_fee = position_value * self.fees['taker']  # Assume taker
            exit_fee = exit_price * trade.quantity * self.fees['taker']
            total_fees = entry_fee + exit_fee

            # 2. Funding costs (if futures and held >8 hours)
            holding_hours = (datetime.utcnow() - trade.opened_at).total_seconds() / 3600
            if holding_hours > 8:
                funding_periods = holding_hours / 8
                funding_cost = position_value * self.fees['funding_rate_avg'] * funding_periods
            else:
                funding_cost = 0

            # 3. Slippage estimate (if not captured in actual fill)
            estimated_slippage = position_value * 0.0005 * 2  # 0.05% each side

            # TOTAL COSTS
            total_costs = total_fees + funding_cost + estimated_slippage

            # NET P&L (REALITY)
            net_pnl = gross_pnl - total_costs
            pnl_percent = (net_pnl / position_value) * 100

            # Update trade record with ACCURATE PnL
            trade.exit_price = exit_price
            trade.pnl = net_pnl  # NET, not gross
            trade.pnl_percent = pnl_percent
            trade.status = 'closed'
            trade.closed_at = datetime.utcnow()

            # Update bot stats with COMPOUNDING
            self.bot.current_balance += net_pnl  # Compound immediately
            self.bot.total_pnl += net_pnl
            self.bot.total_trades += 1
            if net_pnl > 0:
                self.bot.winning_trades += 1
            else:
                self.bot.losing_trades += 1
            self.bot.last_trade_at = datetime.utcnow()

            self.db.commit()

            # Log with cost breakdown
            logger.info(f"✅ Position closed: {trade.symbol} @ ${exit_price:.2f} | Reason: {reason}")
            logger.info(f"💰 P&L: Gross ${gross_pnl:.2f} - Costs ${total_costs:.2f} = Net ${net_pnl:.2f} ({pnl_percent:.2f}%)")
            logger.info(f"   Fees: ${total_fees:.2f} | Funding: ${funding_cost:.2f} | Slippage: ~${estimated_slippage:.2f}")
            logger.info(f"💵 Balance updated: ${self.bot.current_balance:.2f} (compounding enabled)")

            # Cleanup trailing stop tracking
            if trade.id in self.peak_prices:
                del self.peak_prices[trade.id]

        except Exception as e:
            logger.error(f"❌ Failed to close position: {str(e)}")
            self.db.rollback()

    def run_trading_cycle(self):
        """
        Execute one trading cycle
        1. Check open positions
        2. Scan markets for signals
        3. Execute trades if conditions met
        """
        try:
            logger.info(f"🔄 Running trading cycle for bot {self.bot_id} ({self.bot.name})")

            # Step 1: Check and update open positions
            self.check_open_positions()

            # Step 2: Scan configured markets for new signals
            markets = self.config.get('markets', [])

            for symbol in markets:
                try:
                    # Check if we already have an open position in this market
                    existing_position = self.db.query(Trade).filter(
                        Trade.bot_id == self.bot_id,
                        Trade.symbol == symbol,
                        Trade.status == 'open'
                    ).first()

                    if existing_position:
                        logger.info(f"⏸️ Skipping {symbol} - already have open position")
                        continue

                    # Generate signal
                    signal = self.generate_signal(symbol)

                    # Execute trade if signal is strong enough
                    if signal['action'] in ['buy', 'sell']:
                        self.execute_trade(symbol, signal['action'], signal['confidence'])

                except Exception as e:
                    logger.error(f"❌ Error processing {symbol}: {str(e)}")
                    continue

            logger.info(f"✅ Trading cycle completed for bot {self.bot_id}")

        except Exception as e:
            logger.error(f"❌ Trading cycle failed for bot {self.bot_id}: {str(e)}")
