"""
WebSocket Server for Real-Time Dashboard Updates
Pushes live trading signals, executions, and P&L updates to frontend

Features:
- Real-time signal broadcasts
- Live trade execution updates
- Real-time P&L tracking
- Live bot status updates
- Multi-user support
- Room-based broadcasting

Goal: Dashboard updates in <100ms
"""

import asyncio
import json
from typing import Dict, Set
from datetime import datetime
import logging
from dataclasses import asdict

try:
    from fastapi import WebSocket, WebSocketDisconnect
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    WebSocket = None
    WebSocketDisconnect = Exception

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# CONNECTION MANAGER
# ============================================================================

class ConnectionManager:
    """
    Manages WebSocket connections for real-time updates
    """

    def __init__(self):
        # Active connections: {user_id: {connection_id: websocket}}
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}

        # Room subscriptions: {room_name: set(user_ids)}
        self.rooms: Dict[str, Set[str]] = {}

    async def connect(self, websocket: WebSocket, user_id: str, connection_id: str):
        """
        Accept new WebSocket connection

        Args:
            websocket: WebSocket instance
            user_id: User ID
            connection_id: Unique connection ID
        """
        await websocket.accept()

        # Add to active connections
        if user_id not in self.active_connections:
            self.active_connections[user_id] = {}

        self.active_connections[user_id][connection_id] = websocket

        logger.info(f"✅ WebSocket connected: User {user_id}, Connection {connection_id}")
        logger.info(f"   Total connections: {self.get_total_connections()}")

        # Send welcome message
        await self.send_personal_message(
            {
                'type': 'connection',
                'status': 'connected',
                'user_id': user_id,
                'timestamp': datetime.utcnow().isoformat()
            },
            user_id
        )

    def disconnect(self, user_id: str, connection_id: str):
        """
        Remove WebSocket connection

        Args:
            user_id: User ID
            connection_id: Connection ID
        """
        if user_id in self.active_connections:
            if connection_id in self.active_connections[user_id]:
                del self.active_connections[user_id][connection_id]

            # Remove user entry if no more connections
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

        logger.info(f"❌ WebSocket disconnected: User {user_id}, Connection {connection_id}")
        logger.info(f"   Total connections: {self.get_total_connections()}")

    async def join_room(self, user_id: str, room_name: str):
        """
        Join a room for room-based broadcasting

        Args:
            user_id: User ID
            room_name: Room name (e.g., 'bot_123', 'signals')
        """
        if room_name not in self.rooms:
            self.rooms[room_name] = set()

        self.rooms[room_name].add(user_id)

        logger.info(f"👥 User {user_id} joined room '{room_name}'")

    async def leave_room(self, user_id: str, room_name: str):
        """
        Leave a room

        Args:
            user_id: User ID
            room_name: Room name
        """
        if room_name in self.rooms:
            self.rooms[room_name].discard(user_id)

            # Remove empty rooms
            if not self.rooms[room_name]:
                del self.rooms[room_name]

        logger.info(f"👋 User {user_id} left room '{room_name}'")

    async def send_personal_message(self, message: Dict, user_id: str):
        """
        Send message to specific user (all their connections)

        Args:
            message: Message data
            user_id: User ID
        """
        if user_id in self.active_connections:
            # Send to all user's connections
            for connection_id, websocket in self.active_connections[user_id].items():
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending to {user_id}/{connection_id}: {str(e)}")

    async def broadcast_to_room(self, message: Dict, room_name: str):
        """
        Broadcast message to all users in a room

        Args:
            message: Message data
            room_name: Room name
        """
        if room_name not in self.rooms:
            return

        # Send to all users in room
        for user_id in self.rooms[room_name]:
            await self.send_personal_message(message, user_id)

        logger.info(f"📡 Broadcast to room '{room_name}': {len(self.rooms[room_name])} users")

    async def broadcast_to_all(self, message: Dict):
        """
        Broadcast message to all connected users

        Args:
            message: Message data
        """
        for user_id in self.active_connections.keys():
            await self.send_personal_message(message, user_id)

        logger.info(f"📡 Global broadcast: {len(self.active_connections)} users")

    def get_total_connections(self) -> int:
        """Get total number of connections"""
        return sum(len(conns) for conns in self.active_connections.values())


# ============================================================================
# LIVE UPDATE BROADCASTER
# ============================================================================

class LiveUpdateBroadcaster:
    """
    Broadcasts live trading updates via WebSocket
    """

    def __init__(self, connection_manager: ConnectionManager):
        self.manager = connection_manager

    async def broadcast_signal(self, signal: Dict, user_id: str = None):
        """
        Broadcast trading signal

        Args:
            signal: Signal data
            user_id: Specific user (None = broadcast to all)
        """
        message = {
            'type': 'signal',
            'data': signal,
            'timestamp': datetime.utcnow().isoformat()
        }

        if user_id:
            await self.manager.send_personal_message(message, user_id)
        else:
            await self.manager.broadcast_to_all(message)

    async def broadcast_trade_execution(self, trade: Dict, user_id: str = None):
        """
        Broadcast trade execution

        Args:
            trade: Trade data
            user_id: Specific user
        """
        message = {
            'type': 'trade_execution',
            'data': trade,
            'timestamp': datetime.utcnow().isoformat()
        }

        if user_id:
            await self.manager.send_personal_message(message, user_id)
        else:
            # Broadcast to bot-specific room
            bot_id = trade.get('bot_id')
            if bot_id:
                await self.manager.broadcast_to_room(message, f"bot_{bot_id}")

    async def broadcast_pnl_update(self, pnl_data: Dict, user_id: str):
        """
        Broadcast P&L update

        Args:
            pnl_data: P&L data
            user_id: User ID
        """
        message = {
            'type': 'pnl_update',
            'data': pnl_data,
            'timestamp': datetime.utcnow().isoformat()
        }

        await self.manager.send_personal_message(message, user_id)

    async def broadcast_bot_status(self, status: Dict, bot_id: str):
        """
        Broadcast bot status update

        Args:
            status: Status data
            bot_id: Bot ID
        """
        message = {
            'type': 'bot_status',
            'data': status,
            'timestamp': datetime.utcnow().isoformat()
        }

        await self.manager.broadcast_to_room(message, f"bot_{bot_id}")

    async def broadcast_alert(self, alert: Dict, user_id: str):
        """
        Broadcast alert/notification

        Args:
            alert: Alert data
            user_id: User ID
        """
        message = {
            'type': 'alert',
            'data': alert,
            'timestamp': datetime.utcnow().isoformat()
        }

        await self.manager.send_personal_message(message, user_id)


# ============================================================================
# REAL-TIME P&L TRACKER
# ============================================================================

class RealtimePnLTracker:
    """
    Track and broadcast real-time P&L updates
    """

    def __init__(self, broadcaster: LiveUpdateBroadcaster):
        self.broadcaster = broadcaster
        self.running = False

    async def start_tracking(self, user_id: str, bot_id: str, interval_seconds: int = 5):
        """
        Start real-time P&L tracking

        Args:
            user_id: User ID
            bot_id: Bot ID
            interval_seconds: Update interval
        """
        self.running = True
        logger.info(f"📊 Starting real-time P&L tracking for bot {bot_id}")

        while self.running:
            try:
                # Calculate current P&L
                pnl_data = await self._calculate_current_pnl(bot_id)

                # Broadcast update
                await self.broadcaster.broadcast_pnl_update(pnl_data, user_id)

            except Exception as e:
                logger.error(f"Error tracking P&L: {str(e)}")

            await asyncio.sleep(interval_seconds)

    def stop_tracking(self):
        """Stop P&L tracking"""
        self.running = False

    async def _calculate_current_pnl(self, bot_id: str) -> Dict:
        """Calculate current P&L"""
        # In production: Fetch from exchange and database
        # For demo: Return sample data

        import random
        return {
            'bot_id': bot_id,
            'total_pnl': random.uniform(-500, 1500),
            'total_pnl_percent': random.uniform(-5, 15),
            'today_pnl': random.uniform(-100, 300),
            'today_pnl_percent': random.uniform(-1, 3),
            'open_positions': random.randint(0, 5),
            'open_pnl': random.uniform(-200, 400)
        }


# ============================================================================
# FASTAPI WEBSOCKET ENDPOINTS
# ============================================================================

if FASTAPI_AVAILABLE:
    from fastapi import FastAPI

    # Connection manager instance
    manager = ConnectionManager()
    broadcaster = LiveUpdateBroadcaster(manager)

    async def websocket_endpoint(websocket: WebSocket, user_id: str):
        """
        WebSocket endpoint for real-time updates

        Usage:
            ws://localhost:8000/ws/{user_id}
        """
        import uuid
        connection_id = str(uuid.uuid4())

        await manager.connect(websocket, user_id, connection_id)

        try:
            while True:
                # Receive messages from client
                data = await websocket.receive_json()

                # Handle different message types
                msg_type = data.get('type')

                if msg_type == 'subscribe_bot':
                    # Subscribe to bot updates
                    bot_id = data.get('bot_id')
                    await manager.join_room(user_id, f"bot_{bot_id}")

                    await websocket.send_json({
                        'type': 'subscribed',
                        'bot_id': bot_id
                    })

                elif msg_type == 'unsubscribe_bot':
                    # Unsubscribe from bot updates
                    bot_id = data.get('bot_id')
                    await manager.leave_room(user_id, f"bot_{bot_id}")

                    await websocket.send_json({
                        'type': 'unsubscribed',
                        'bot_id': bot_id
                    })

                elif msg_type == 'ping':
                    # Heartbeat
                    await websocket.send_json({'type': 'pong'})

        except WebSocketDisconnect:
            manager.disconnect(user_id, connection_id)


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

async def example_websocket_usage():
    """Example WebSocket usage"""

    print("\n" + "="*80)
    print("WEBSOCKET REAL-TIME UPDATES - DEMO")
    print("="*80)

    # Create manager and broadcaster
    manager = ConnectionManager()
    broadcaster = LiveUpdateBroadcaster(manager)

    # Simulate broadcasting updates
    print("\n📡 Simulating real-time broadcasts...")

    # Signal broadcast
    signal = {
        'symbol': 'BTC/USDT',
        'type': 'BUY',
        'price': 50000,
        'confidence': 0.85
    }
    print(f"\n🔔 Broadcasting signal: {signal}")
    await broadcaster.broadcast_signal(signal)

    # Trade execution broadcast
    trade = {
        'bot_id': 'bot_123',
        'symbol': 'BTC/USDT',
        'side': 'buy',
        'price': 50050,
        'size': 0.1,
        'status': 'filled'
    }
    print(f"\n✅ Broadcasting trade execution: {trade}")
    await broadcaster.broadcast_trade_execution(trade)

    print("\n✅ WebSocket broadcasts complete")


if __name__ == "__main__":
    asyncio.run(example_websocket_usage())
