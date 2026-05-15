#!/bin/bash

# ============================================================================
# Trading Bot Engine Startup Script
# Starts Celery worker and beat scheduler for multi-tenant bot execution
# ============================================================================

echo "🚀 Starting Trading Bot Engine..."

# Check if Redis is running
if ! redis-cli ping > /dev/null 2>&1; then
    echo "❌ Redis is not running! Please start Redis first:"
    echo "   brew services start redis  # macOS"
    echo "   sudo systemctl start redis  # Linux"
    exit 1
fi

echo "✅ Redis is running"

# Check if PostgreSQL is running
if ! pg_isready > /dev/null 2>&1; then
    echo "⚠️ PostgreSQL doesn't seem to be running"
    echo "   Make sure your database is accessible"
fi

# Export environment variables if .env exists
if [ -f .env ]; then
    echo "📝 Loading environment variables from .env"
    export $(cat .env | grep -v '^#' | xargs)
fi

# Kill existing Celery processes (for development)
echo "🧹 Cleaning up existing Celery processes..."
pkill -f 'celery worker' 2>/dev/null
pkill -f 'celery beat' 2>/dev/null
sleep 2

# Start Celery worker in background
echo "🔧 Starting Celery worker..."
celery -A celery_app worker \
    --loglevel=info \
    --concurrency=4 \
    --logfile=logs/celery_worker.log \
    --pidfile=logs/celery_worker.pid &

WORKER_PID=$!
echo "✅ Celery worker started (PID: $WORKER_PID)"

# Wait a moment for worker to initialize
sleep 3

# Start Celery beat scheduler in background
echo "⏰ Starting Celery beat scheduler..."
celery -A celery_app beat \
    --loglevel=info \
    --logfile=logs/celery_beat.log \
    --pidfile=logs/celery_beat.pid &

BEAT_PID=$!
echo "✅ Celery beat started (PID: $BEAT_PID)"

echo ""
echo "🎉 Trading Bot Engine is now running!"
echo ""
echo "📊 Monitoring:"
echo "   - Worker log: tail -f logs/celery_worker.log"
echo "   - Beat log:   tail -f logs/celery_beat.log"
echo "   - Flower UI:  celery -A celery_app flower"
echo ""
echo "🛑 To stop:"
echo "   kill $WORKER_PID $BEAT_PID"
echo "   or: pkill -f 'celery'"
echo ""

# Keep script running and monitor processes
trap "echo '🛑 Shutting down...'; kill $WORKER_PID $BEAT_PID 2>/dev/null; exit 0" SIGINT SIGTERM

# Wait for processes
wait
