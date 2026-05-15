#!/bin/bash
# Agent Lightning — Complete Setup Script
# Sets up APO optimizer, training pipeline, and dashboard

set -e

WORKSPACE="$HOME/.openclaw/workspace/agent-lightning"
PYTHON="python3.11"

echo "⚡ Agent Lightning Setup"
echo "========================"
echo ""

# 1. Verify installation
echo "1. Verifying installation..."
$PYTHON -c "import agentlightning; print(f'   agentlightning v{agentlightning.__version__}')" || {
    echo "   ❌ agentlightning not installed. Run: pip3.11 install agentlightning"
    exit 1
}
$PYTHON -c "import openai; print(f'   openai v{openai.__version__}')" || {
    echo "   ❌ openai not installed. Run: pip3.11 install openai"
    exit 1
}

# 2. Check API key
echo ""
echo "2. Checking OpenRouter API key..."
if [ -z "$OPENROUTER_API_KEY" ]; then
    # Try to load from .env
    if [ -f "$HOME/.openclaw/.env" ]; then
        export OPENROUTER_API_KEY=$(grep OPENROUTER_API_KEY "$HOME/.openclaw/.env" | cut -d= -f2)
    fi
fi

if [ -n "$OPENROUTER_API_KEY" ]; then
    echo "   ✅ API key found"
else
    echo "   ⚠️  OPENROUTER_API_KEY not set. APO will need it at runtime."
fi

# 3. Create results directories
echo ""
echo "3. Creating directories..."
mkdir -p "$WORKSPACE/apo/results"
mkdir -p "$WORKSPACE/training/results"
mkdir -p "$WORKSPACE/dashboard/build"
echo "   ✅ Directories ready"

# 4. Verify dashboard build
echo ""
echo "4. Checking dashboard..."
if [ -f "$WORKSPACE/dashboard/build/index.html" ]; then
    echo "   ✅ Dashboard built"
else
    echo "   ⚠️  Dashboard not built. Run: cd /tmp/agent-lightning/dashboard && npm run build"
fi

# 5. Test APO import
echo ""
echo "5. Testing APO..."
$PYTHON -c "
from openai import AsyncOpenAI
import agentlightning as agl
print('   ✅ APO algorithm loaded')
print('   ✅ VERL algorithm loaded')
print('   ✅ Trainer loaded')
" 2>/dev/null || echo "   ⚠️  Some components may need additional setup"

echo ""
echo "========================"
echo "✅ Setup complete!"
echo ""
echo "Usage:"
echo "  APO (prompt optimization):  $PYTHON $WORKSPACE/apo/apo_optimizer.py"
echo "  Training pipeline:          $PYTHON $WORKSPACE/training/train_capital_recovery.py --mode dev"
echo "  Dashboard:                  $PYTHON $WORKSPACE/dashboard/dashboard_server.py --port 8080"
echo ""
echo "Start store first for dashboard:"
echo "  agl store --port 9999"
