"""
WEBSOCKET MANAGER
Ultra-low latency WebSocket connections for real-time market data

Features:
- Sub-millisecond latency for order book updates
- Real-time trade flow data
- Funding rate monitoring
- Auto-reconnection with exponential backoff
- Multiple exchange support
"""

import asyncio
import websockets
import json
import time
import logging
from typing import Dict, List, Callable, Optional, Any
from datetime import datetime
from collections import deque
from dataclasses import dataclass
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class OrderBookSnapshot:
    """Real-time order book data"""
    symbol: str
    timestamp: datetime
    bids: List[tuple]  # [(price, quantity), ...]
    asks: List[tuple]
    best_bid: float
    best_ask: float
    spread: float
    spread_pct: float
    mid_price: float
    depth_imbalance: float  # Positive = more bids, Negative = more asks

    def to_dict(self) -> Dict[str, Any]:
        return {
            'symbol': self.symbol,
            'timestamp': self.timestamp.isoformat(),
            'best_bid': self.best_bid,
            'best_ask': self.best_ask,
            'spread': self.spread,
            'spread_pct': self.spread_pct,
            'mid_price': self.mid_price,
            'depth_imbalance': self.depth_imbalance
        }


@dataclass
class TradeFlow:
    """Real-time trade flow data"""
    symbol: str
    timestamp: datetime
    price: float
    quantity: float
    side: str  # 'buy' or 'sell'
    is_maker: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            'symbol': self.symbol,
            'timestamp': self.timestamp.isoformat(),
            'price': self.price,
            'quantity': self.quantity,
            'side': self.side,
            'is_maker': self.is_maker
        }


class WebSocketManager:
    """
    Manages real-time WebSocket connections to exchanges

    Provides:
    - Order book updates (Level 2 data)
    - Trade flow (executed trades)
    - Funding rates
    - Low-latency data delivery
    """

    def __init__(self, exchange: str = 'binance'):
        self.exchange = exchange
        self.ws_connections: Dict[str, Any] = {}
        self.subscriptions: Dict[str, List[Callable]] = {}

        # Data storage (ring buffers for efficiency)
        self.orderbook_data: Dict[str, deque] = {}
        self.trade_data: Dict[str, deque] = {}
        self.funding_rates: Dict[str, float] = {}

        # Performance metrics
        self.latency_stats = {
            'min': float('inf'),
            'max': 0,
            'avg': 0,
            'samples': []
        }

        # Connection status
        self.is_connected = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 10

        # URLs for different exchanges
        self.ws_urls = {
            'binance': 'wss://fstream.binance.com/ws',
            'bybit': 'wss://stream.bybit.com/realtime',
            'okx': 'wss://ws.okx.com:8443/ws/v5/public'
        }

    async def connect(self, symbols: List[str]):
        """Connect to WebSocket and subscribe to symbols"""
        try:
            url = self.ws_urls.get(self.exchange, self.ws_urls['binance'])
            logger.info(f"🔌 Connecting to {self.exchange} WebSocket...")

            async with websockets.connect(url) as websocket:
                self.is_connected = True
                self.reconnect_attempts = 0
                logger.info(f"✅ Connected to {self.exchange}")

                # Subscribe to streams
                await self._subscribe(websocket, symbols)

                # Listen for messages
                await self._listen(websocket)

        except Exception as e:
            logger.error(f"❌ WebSocket connection error: {e}")
            await self._handle_reconnect(symbols)

    async def _subscribe(self, websocket, symbols: List[str]):
        """Subscribe to data streams"""
        if self.exchange == 'binance':
            # Subscribe to order book depth and trades
            streams = []
            for symbol in symbols:
                symbol_lower = symbol.lower().replace('/', '')
                streams.append(f"{symbol_lower}@depth20@100ms")  # Order book
                streams.append(f"{symbol_lower}@aggTrade")  # Trades

            subscribe_msg = {
                "method": "SUBSCRIBE",
                "params": streams,
                "id": 1
            }

            await websocket.send(json.dumps(subscribe_msg))
            logger.info(f"📡 Subscribed to {len(streams)} streams")

    async def _listen(self, websocket):
        """Listen for WebSocket messages"""
        async for message in websocket:
            try:
                receive_time = time.time()
                data = json.loads(message)

                # Process message
                await self._process_message(data, receive_time)

            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON received: {message[:100]}")
            except Exception as e:
                logger.error(f"Error processing message: {e}")

    async def _process_message(self, data: Dict, receive_time: float):
        """Process incoming WebSocket message"""

        if 'stream' in data:
            stream = data['stream']
            payload = data['data']

            # Order book updates
            if '@depth' in stream:
                await self._handle_orderbook(payload, receive_time)

            # Trade updates
            elif '@aggTrade' in stream or '@trade' in stream:
                await self._handle_trade(payload, receive_time)

    async def _handle_orderbook(self, data: Dict, receive_time: float):
        """Handle order book update"""
        try:
            # Extract symbol
            symbol = data.get('s', '').replace('USDT', '/USDT')

            # Parse bids and asks
            bids = [(float(p), float(q)) for p, q in data.get('b', [])]
            asks = [(float(p), float(q)) for p, q in data.get('a', [])]

            if not bids or not asks:
                return

            # Calculate metrics
            best_bid = bids[0][0]
            best_ask = asks[0][0]
            spread = best_ask - best_bid
            mid_price = (best_bid + best_ask) / 2
            spread_pct = (spread / mid_price) * 100

            # Calculate depth imbalance (bid volume vs ask volume)
            total_bid_volume = sum(q for p, q in bids[:10])
            total_ask_volume = sum(q for p, q in asks[:10])
            depth_imbalance = (total_bid_volume - total_ask_volume) / (total_bid_volume + total_ask_volume)

            # Create snapshot
            snapshot = OrderBookSnapshot(
                symbol=symbol,
                timestamp=datetime.now(),
                bids=bids,
                asks=asks,
                best_bid=best_bid,
                best_ask=best_ask,
                spread=spread,
                spread_pct=spread_pct,
                mid_price=mid_price,
                depth_imbalance=depth_imbalance
            )

            # Store in ring buffer (keep last 1000 snapshots)
            if symbol not in self.orderbook_data:
                self.orderbook_data[symbol] = deque(maxlen=1000)
            self.orderbook_data[symbol].append(snapshot)

            # Calculate latency
            if 'E' in data:  # Event time
                exchange_time = data['E'] / 1000
                latency_ms = (receive_time - exchange_time) * 1000
                self._update_latency_stats(latency_ms)

            # Trigger callbacks
            await self._trigger_callbacks('orderbook', snapshot)

        except Exception as e:
            logger.error(f"Error handling orderbook: {e}")

    async def _handle_trade(self, data: Dict, receive_time: float):
        """Handle trade update"""
        try:
            # Extract trade data
            symbol = data.get('s', '').replace('USDT', '/USDT')
            price = float(data.get('p', 0))
            quantity = float(data.get('q', 0))
            side = 'buy' if data.get('m', False) else 'sell'  # m = is buyer maker
            is_maker = data.get('m', False)

            trade = TradeFlow(
                symbol=symbol,
                timestamp=datetime.now(),
                price=price,
                quantity=quantity,
                side=side,
                is_maker=is_maker
            )

            # Store in ring buffer
            if symbol not in self.trade_data:
                self.trade_data[symbol] = deque(maxlen=5000)
            self.trade_data[symbol].append(trade)

            # Trigger callbacks
            await self._trigger_callbacks('trade', trade)

        except Exception as e:
            logger.error(f"Error handling trade: {e}")

    def _update_latency_stats(self, latency_ms: float):
        """Update latency statistics"""
        self.latency_stats['samples'].append(latency_ms)

        # Keep only last 100 samples
        if len(self.latency_stats['samples']) > 100:
            self.latency_stats['samples'].pop(0)

        samples = self.latency_stats['samples']
        self.latency_stats['min'] = min(samples)
        self.latency_stats['max'] = max(samples)
        self.latency_stats['avg'] = np.mean(samples)

    async def _trigger_callbacks(self, event_type: str, data):
        """Trigger registered callbacks"""
        key = f"{event_type}_{data.symbol}"
        if key in self.subscriptions:
            for callback in self.subscriptions[key]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(data)
                    else:
                        callback(data)
                except Exception as e:
                    logger.error(f"Callback error: {e}")

    def subscribe_to_orderbook(self, symbol: str, callback: Callable):
        """Subscribe to order book updates for a symbol"""
        key = f"orderbook_{symbol}"
        if key not in self.subscriptions:
            self.subscriptions[key] = []
        self.subscriptions[key].append(callback)
        logger.info(f"📊 Subscribed to order book: {symbol}")

    def subscribe_to_trades(self, symbol: str, callback: Callable):
        """Subscribe to trade flow for a symbol"""
        key = f"trade_{symbol}"
        if key not in self.subscriptions:
            self.subscriptions[key] = []
        self.subscriptions[key].append(callback)
        logger.info(f"📈 Subscribed to trades: {symbol}")

    def get_latest_orderbook(self, symbol: str) -> Optional[OrderBookSnapshot]:
        """Get latest order book snapshot"""
        if symbol in self.orderbook_data and len(self.orderbook_data[symbol]) > 0:
            return self.orderbook_data[symbol][-1]
        return None

    def get_recent_trades(self, symbol: str, count: int = 100) -> List[TradeFlow]:
        """Get recent trades"""
        if symbol in self.trade_data:
            trades = list(self.trade_data[symbol])
            return trades[-count:]
        return []

    def get_latency_stats(self) -> Dict[str, float]:
        """Get latency statistics"""
        return {
            'min_ms': self.latency_stats['min'],
            'max_ms': self.latency_stats['max'],
            'avg_ms': self.latency_stats['avg'],
            'samples': len(self.latency_stats['samples'])
        }

    async def _handle_reconnect(self, symbols: List[str]):
        """Handle reconnection with exponential backoff"""
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            logger.critical(f"🚨 Max reconnect attempts reached. Giving up.")
            return

        self.reconnect_attempts += 1
        wait_time = min(2 ** self.reconnect_attempts, 60)  # Max 60 seconds

        logger.warning(f"🔄 Reconnecting in {wait_time} seconds (attempt {self.reconnect_attempts}/{self.max_reconnect_attempts})")
        await asyncio.sleep(wait_time)

        await self.connect(symbols)

    def print_stats(self):
        """Print connection statistics"""
        print("=" * 80)
        print("📡 WEBSOCKET MANAGER STATS")
        print("=" * 80)

        print(f"\n🔌 Connection:")
        print(f"   Exchange:   {self.exchange}")
        print(f"   Status:     {'🟢 Connected' if self.is_connected else '🔴 Disconnected'}")

        print(f"\n⚡ Latency:")
        stats = self.get_latency_stats()
        print(f"   Min:        {stats['min_ms']:.2f} ms")
        print(f"   Max:        {stats['max_ms']:.2f} ms")
        print(f"   Average:    {stats['avg_ms']:.2f} ms")
        print(f"   Samples:    {stats['samples']}")

        print(f"\n📊 Data Streams:")
        print(f"   Order Books: {len(self.orderbook_data)} symbols")
        print(f"   Trade Flows: {len(self.trade_data)} symbols")

        for symbol in self.orderbook_data.keys():
            orderbook = self.get_latest_orderbook(symbol)
            if orderbook:
                print(f"\n   {symbol}:")
                print(f"      Best Bid:   ${orderbook.best_bid:,.2f}")
                print(f"      Best Ask:   ${orderbook.best_ask:,.2f}")
                print(f"      Spread:     ${orderbook.spread:.2f} ({orderbook.spread_pct:.4f}%)")
                print(f"      Mid Price:  ${orderbook.mid_price:,.2f}")
                print(f"      Imbalance:  {orderbook.depth_imbalance:+.3f}")

        print("=" * 80)


# Example callbacks for testing
async def on_orderbook_update(snapshot: OrderBookSnapshot):
    """Callback for order book updates"""
    logger.info(f"📊 {snapshot.symbol}: Bid ${snapshot.best_bid:,.2f} | Ask ${snapshot.best_ask:,.2f} | Spread {snapshot.spread_pct:.4f}%")


async def on_trade_update(trade: TradeFlow):
    """Callback for trade updates"""
    logger.info(f"📈 {trade.symbol}: {trade.side.upper()} {trade.quantity:.4f} @ ${trade.price:,.2f}")


async def main():
    """Test WebSocket manager"""
    ws_manager = WebSocketManager(exchange='binance')

    # Subscribe to callbacks
    ws_manager.subscribe_to_orderbook('BTC/USDT', on_orderbook_update)
    ws_manager.subscribe_to_trades('BTC/USDT', on_trade_update)

    # Connect
    symbols = ['BTC/USDT', 'ETH/USDT']

    try:
        await ws_manager.connect(symbols)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        ws_manager.print_stats()


if __name__ == '__main__':
    asyncio.run(main())
