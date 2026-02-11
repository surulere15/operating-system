#!/usr/bin/env python3
"""
BYBIT FUTURES INTEGRATION
Handles authenticated trading with leverage for $100 capital deployment
"""

import ccxt
import os
import time
from datetime import datetime
from typing import Dict, Optional, List
import json


class BybitFuturesTrader:
    """Bybit Futures trading with leverage"""

    def __init__(self,
                 api_key: Optional[str] = None,
                 api_secret: Optional[str] = None,
                 testnet: bool = True,
                 capital: float = 100.0):
        """
        Initialize Bybit Futures trader

        Args:
            api_key: Bybit API key (or set BYBIT_API_KEY env var)
            api_secret: Bybit API secret (or set BYBIT_API_SECRET env var)
            testnet: Use testnet (True) or live (False)
            capital: Starting capital in USDT
        """
        self.capital = capital
        self.testnet = testnet

        # Get API credentials
        self.api_key = api_key or os.getenv('BYBIT_API_KEY')
        self.api_secret = api_secret or os.getenv('BYBIT_API_SECRET')

        # Initialize exchange
        self.exchange = self._init_exchange()

        # Trading state
        self.positions = {}  # symbol -> position info
        self.orders = {}     # order_id -> order info

        # Risk limits (for $100 capital)
        self.max_daily_loss = 10.0  # Max $10 loss per day
        self.max_position_loss = 3.0  # Max $3 loss per trade
        self.max_positions = 2  # Max 2 open positions
        self.daily_loss = 0.0

    def _init_exchange(self):
        """Initialize CCXT Bybit Futures exchange"""
        if self.testnet:
            exchange = ccxt.bybit({
                'apiKey': self.api_key,
                'secret': self.api_secret,
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'linear'  # USDT perpetuals
                }
            })
            exchange.set_sandbox_mode(True)
        else:
            exchange = ccxt.bybit({
                'apiKey': self.api_key,
                'secret': self.api_secret,
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'linear'  # USDT perpetuals
                }
            })

        return exchange

    def get_account_balance(self) -> Dict:
        """Get account balance"""
        try:
            balance = self.exchange.fetch_balance()

            # For Bybit Unified Trading Account, balance is in 'info' field
            if 'info' in balance and 'result' in balance['info']:
                result = balance['info']['result']
                if 'list' in result and len(result['list']) > 0:
                    account = result['list'][0]
                    total_equity = float(account.get('totalEquity', 0))
                    available_balance = float(account.get('totalAvailableBalance', total_equity))

                    return {
                        'total': total_equity,
                        'available': available_balance,
                        'margin_used': total_equity - available_balance,
                        'positions': len(self.positions)
                    }

            # Fallback to standard CCXT parsing
            usdt_balance = balance['USDT']['free'] if 'USDT' in balance else 0
            return {
                'total': usdt_balance,
                'available': usdt_balance - self.calculate_margin_used(),
                'margin_used': self.calculate_margin_used(),
                'positions': len(self.positions)
            }
        except Exception as e:
            print(f"❌ Error fetching balance: {e}")
            return {'total': 0, 'available': 0, 'margin_used': 0, 'positions': 0}

    def calculate_margin_used(self) -> float:
        """Calculate total margin used by open positions"""
        total_margin = 0.0
        for symbol, pos in self.positions.items():
            if pos.get('size', 0) != 0:
                total_margin += pos.get('margin', 0)
        return total_margin

    def set_leverage(self, symbol: str, leverage: int):
        """Set leverage for a symbol"""
        try:
            self.exchange.set_leverage(leverage, symbol)
            print(f"✅ Set {leverage}x leverage for {symbol}")
            return True
        except Exception as e:
            print(f"❌ Error setting leverage for {symbol}: {e}")
            return False

    def calculate_position_size(self,
                                signal: Dict,
                                position_pct: float = 0.30,
                                leverage: int = 10) -> Dict:
        """Calculate position size for a signal"""
        balance = self.get_account_balance()
        available = balance['available']

        position_capital = min(available * position_pct, available)
        position_size_usd = position_capital * leverage

        price = signal['price']
        quantity = position_size_usd / price

        stop_loss_price = signal['stop_loss']
        stop_loss_pct = abs(price - stop_loss_price) / price
        max_loss_usd = position_size_usd * stop_loss_pct

        if max_loss_usd > self.max_position_loss:
            scale_factor = self.max_position_loss / max_loss_usd
            position_size_usd *= scale_factor
            quantity *= scale_factor
            max_loss_usd = self.max_position_loss

        return {
            'symbol': signal['symbol'],
            'side': 'buy' if signal['type'] == 'BUY' else 'sell',
            'quantity': quantity,
            'position_size_usd': position_size_usd,
            'margin_required': position_capital,
            'leverage': leverage,
            'entry_price': price,
            'stop_loss': stop_loss_price,
            'take_profit_1': signal['take_profit_1'],
            'take_profit_2': signal['take_profit_2'],
            'take_profit_3': signal['take_profit_3'],
            'max_loss_usd': max_loss_usd,
            'potential_profit_1': (signal['take_profit_1'] - price) / price * position_size_usd if signal['type'] == 'BUY'
                                  else (price - signal['take_profit_1']) / price * position_size_usd,
        }

    def check_risk_limits(self) -> bool:
        """Check if we can take new positions"""
        if self.daily_loss >= self.max_daily_loss:
            print(f"🛑 Daily loss limit reached: ${self.daily_loss:.2f} / ${self.max_daily_loss:.2f}")
            return False

        active_positions = len([p for p in self.positions.values() if p.get('size', 0) != 0])
        if active_positions >= self.max_positions:
            print(f"🛑 Max positions limit: {active_positions} / {self.max_positions}")
            return False

        return True

    def open_position(self, signal: Dict, leverage: int = 10) -> Optional[Dict]:
        """Open a position based on signal"""
        if not self.check_risk_limits():
            return None

        position_info = self.calculate_position_size(signal, leverage=leverage)
        symbol = signal['symbol']

        self.set_leverage(symbol, leverage)

        try:
            side = position_info['side']
            quantity = position_info['quantity']

            print(f"\n📤 Opening {side.upper()} position:")
            print(f"   Symbol: {symbol}")
            print(f"   Quantity: {quantity:.6f}")
            print(f"   Position Size: ${position_info['position_size_usd']:.2f}")
            print(f"   Leverage: {leverage}x")
            print(f"   Max Loss: ${position_info['max_loss_usd']:.2f}")

            order = self.exchange.create_market_order(
                symbol=symbol,
                side=side,
                amount=quantity
            )

            print(f"✅ Order executed: {order['id']}")

            self.orders[order['id']] = {
                **order,
                'signal': signal,
                'position_info': position_info,
                'timestamp': datetime.now().isoformat()
            }

            self.positions[symbol] = {
                'symbol': symbol,
                'side': side,
                'size': quantity,
                'entry_price': order.get('average', signal['price']),
                'leverage': leverage,
                'margin': position_info['margin_required'],
                'stop_loss': position_info['stop_loss'],
                'take_profits': [
                    position_info['take_profit_1'],
                    position_info['take_profit_2'],
                    position_info['take_profit_3']
                ],
                'unrealized_pnl': 0.0,
                'order_id': order['id']
            }

            self.place_stop_loss(symbol, position_info)
            self.place_take_profits(symbol, position_info)

            return order

        except Exception as e:
            print(f"❌ Error opening position: {e}")
            return None

    def place_stop_loss(self, symbol: str, position_info: Dict):
        """Place stop loss order"""
        try:
            side = 'sell' if position_info['side'] == 'buy' else 'buy'

            stop_order = self.exchange.create_order(
                symbol=symbol,
                type='market',
                side=side,
                amount=position_info['quantity'],
                params={
                    'stopLoss': position_info['stop_loss'],
                    'reduceOnly': True
                }
            )

            print(f"✅ Stop loss placed at ${position_info['stop_loss']:.4f}")
            return stop_order

        except Exception as e:
            print(f"⚠️  Could not place stop loss: {e}")
            return None

    def place_take_profits(self, symbol: str, position_info: Dict):
        """Place take profit orders"""
        try:
            side = 'sell' if position_info['side'] == 'buy' else 'buy'
            quantity_per_tp = position_info['quantity'] / 3

            for i, tp_price in enumerate([
                position_info['take_profit_1'],
                position_info['take_profit_2'],
                position_info['take_profit_3']
            ]):
                tp_order = self.exchange.create_order(
                    symbol=symbol,
                    type='limit',
                    side=side,
                    amount=quantity_per_tp,
                    price=tp_price,
                    params={'reduceOnly': True}
                )

                print(f"✅ Take Profit {i+1} placed at ${tp_price:.4f}")

        except Exception as e:
            print(f"⚠️  Could not place take profits: {e}")

    def close_position(self, symbol: str, reason: str = "Manual close") -> Optional[Dict]:
        """Close an open position"""
        if symbol not in self.positions:
            print(f"❌ No position for {symbol}")
            return None

        pos = self.positions[symbol]

        try:
            side = 'sell' if pos['side'] == 'buy' else 'buy'

            close_order = self.exchange.create_market_order(
                symbol=symbol,
                side=side,
                amount=pos['size'],
                params={'reduceOnly': True}
            )

            entry = pos['entry_price']
            exit_price = close_order.get('average', 0)

            if pos['side'] == 'buy':
                pnl = (exit_price - entry) / entry * pos['size'] * entry
            else:
                pnl = (entry - exit_price) / entry * pos['size'] * entry

            pnl_pct = pnl / pos['margin'] * 100

            print(f"\n💰 Position Closed: {symbol}")
            print(f"   Entry: ${entry:.4f}")
            print(f"   Exit: ${exit_price:.4f}")
            print(f"   P&L: ${pnl:.2f} ({pnl_pct:+.2f}%)")
            print(f"   Reason: {reason}")

            if pnl < 0:
                self.daily_loss += abs(pnl)

            del self.positions[symbol]
            self.cancel_orders_for_symbol(symbol)

            return {
                'symbol': symbol,
                'pnl': pnl,
                'pnl_pct': pnl_pct,
                'reason': reason,
                'close_order': close_order
            }

        except Exception as e:
            print(f"❌ Error closing position: {e}")
            return None

    def cancel_orders_for_symbol(self, symbol: str):
        """Cancel all open orders for a symbol"""
        try:
            self.exchange.cancel_all_orders(symbol)
            print(f"✅ Cancelled all orders for {symbol}")
        except Exception as e:
            print(f"⚠️  Error cancelling orders: {e}")

    def monitor_positions(self):
        """Monitor open positions and update P&L"""
        for symbol, pos in list(self.positions.items()):
            try:
                ticker = self.exchange.fetch_ticker(symbol)
                current_price = ticker['last']

                entry = pos['entry_price']

                if pos['side'] == 'buy':
                    unrealized_pnl = (current_price - entry) / entry * pos['size'] * entry
                else:
                    unrealized_pnl = (entry - current_price) / entry * pos['size'] * entry

                pos['unrealized_pnl'] = unrealized_pnl
                pos['current_price'] = current_price

            except Exception as e:
                print(f"⚠️  Error monitoring {symbol}: {e}")

    def get_position_summary(self) -> str:
        """Get summary of all positions"""
        balance = self.get_account_balance()

        summary = f"\n{'='*60}\n"
        summary += f"💼 ACCOUNT SUMMARY (BYBIT)\n"
        summary += f"{'='*60}\n"
        summary += f"Total Balance: ${balance['total']:.2f} USDT\n"
        summary += f"Available: ${balance['available']:.2f}\n"
        summary += f"Margin Used: ${balance['margin_used']:.2f}\n"
        summary += f"Daily Loss: ${self.daily_loss:.2f} / ${self.max_daily_loss:.2f}\n"
        summary += f"Open Positions: {len(self.positions)}\n"

        if self.positions:
            summary += f"\n📊 POSITIONS:\n"
            summary += f"{'-'*60}\n"

            for symbol, pos in self.positions.items():
                pnl_pct = (pos['unrealized_pnl'] / pos['margin'] * 100) if pos.get('margin', 0) > 0 else 0

                summary += f"{symbol} | {pos['side'].upper()}\n"
                summary += f"  Entry: ${pos['entry_price']:.4f} | Current: ${pos.get('current_price', 0):.4f}\n"
                summary += f"  Size: {pos['size']:.6f} | Leverage: {pos['leverage']}x\n"
                summary += f"  P&L: ${pos['unrealized_pnl']:.2f} ({pnl_pct:+.2f}%)\n"
                summary += f"  SL: ${pos['stop_loss']:.4f}\n"
                summary += f"{'-'*60}\n"

        return summary

    def save_state(self, filepath: str = "/tmp/trading_state_bybit.json"):
        """Save trading state to file"""
        state = {
            'timestamp': datetime.now().isoformat(),
            'capital': self.capital,
            'daily_loss': self.daily_loss,
            'positions': self.positions,
            'orders': self.orders
        }

        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2)

        print(f"💾 State saved to {filepath}")


def test_connection():
    """Test Bybit Futures connection"""
    print("\n🔧 Testing Bybit Futures Connection...\n")

    api_key = os.getenv('BYBIT_API_KEY')
    api_secret = os.getenv('BYBIT_API_SECRET')

    if not api_key or not api_secret:
        print("⚠️  WARNING: Bybit API keys not found!")
        print("\nTo set up Bybit API keys:")
        print("1. Go to bybit.com → API Management")
        print("2. Create new API key")
        print("3. Enable Derivatives trading")
        print("4. Set environment variables:")
        print("   export BYBIT_API_KEY='your_key'")
        print("   export BYBIT_API_SECRET='your_secret'")
        print("\nFor now, using testnet mode (demo trading)")

    trader = BybitFuturesTrader(testnet=True, capital=100.0)

    try:
        balance = trader.get_account_balance()
        print(f"✅ Connection successful!")
        print(f"   Balance: ${balance['total']:.2f} USDT")
        print(f"   Mode: {'TESTNET (Demo)' if trader.testnet else 'LIVE'}")
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False


if __name__ == "__main__":
    test_connection()
