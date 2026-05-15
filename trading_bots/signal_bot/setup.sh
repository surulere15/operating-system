#!/bin/bash
# @AlphaEdgeSignals - Automated Setup Script
# This script installs dependencies and tests the configuration

echo "============================================================"
echo "🚀 @ALPHAEDGESIGNALS - SETUP & DEPLOYMENT"
echo "============================================================"
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✅ Python $python_version detected"
echo ""

# Install dependencies
echo "Installing dependencies..."
pip3 install ccxt pandas numpy --quiet

if [ $? -eq 0 ]; then
    echo "✅ Dependencies installed successfully"
else
    echo "❌ Failed to install dependencies"
    exit 1
fi
echo ""

# Check for API keys
echo "Checking for Binance API credentials..."
if [ -z "$BINANCE_API_KEY" ] || [ -z "$BINANCE_API_SECRET" ]; then
    echo "⚠️  WARNING: Binance API keys not found"
    echo ""
    echo "To set up API keys:"
    echo "1. Get API keys from binance.com → API Management"
    echo "2. Add to your shell profile (~/.bashrc or ~/.zshrc):"
    echo ""
    echo "   export BINANCE_API_KEY=\"your_key_here\""
    echo "   export BINANCE_API_SECRET=\"your_secret_here\""
    echo ""
    echo "3. Reload: source ~/.bashrc"
    echo ""
    echo "For now, continuing with testnet mode (no API keys needed)"
else
    echo "✅ API keys found"
    echo "   Key: ${BINANCE_API_KEY:0:10}..."
fi
echo ""

# Test Binance connection
echo "Testing Binance connection..."
python3 binance_futures.py

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Connection test passed!"
else
    echo ""
    echo "⚠️  Connection test had issues (check above)"
fi
echo ""

# Run signal bot test (one scan)
echo "Testing signal generation (one scan)..."
python3 crypto_signals.py

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Signal bot test passed!"
else
    echo ""
    echo "❌ Signal bot test failed"
    exit 1
fi
echo ""

echo "============================================================"
echo "🎉 SETUP COMPLETE!"
echo "============================================================"
echo ""
echo "Next steps:"
echo ""
echo "1. TESTNET MODE (recommended first):"
echo "   python3 deploy_live.py --capital 100"
echo ""
echo "2. LIVE MODE (real money):"
echo "   python3 deploy_live.py --capital 100 --live"
echo ""
echo "3. ONE-TIME SCAN (no continuous trading):"
echo "   python3 deploy_live.py --capital 100 --once"
echo ""
echo "For more options, see DEPLOYMENT_GUIDE.md"
echo ""
echo "Good luck! 🚀"
echo ""
