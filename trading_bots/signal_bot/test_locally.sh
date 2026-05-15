#!/bin/bash

# Local Testing Script for Crypto Signal Bot
# Edit the values below, then run: ./test_locally.sh

echo "🤖 CRYPTO SIGNAL BOT - LOCAL TEST"
echo "=================================="
echo ""

# EDIT THESE VALUES:
export TELEGRAM_BOT_TOKEN="YOUR_BOT_TOKEN_HERE"
export TELEGRAM_CHANNEL_ID="YOUR_CHANNEL_ID_HERE"

# Check if values are set
if [ "$TELEGRAM_BOT_TOKEN" = "YOUR_BOT_TOKEN_HERE" ]; then
    echo "❌ ERROR: Please edit test_locally.sh and set TELEGRAM_BOT_TOKEN"
    echo ""
    echo "Get your token from @BotFather on Telegram"
    echo "Then edit this file and replace YOUR_BOT_TOKEN_HERE"
    echo ""
    exit 1
fi

if [ "$TELEGRAM_CHANNEL_ID" = "YOUR_CHANNEL_ID_HERE" ]; then
    echo "❌ ERROR: Please edit test_locally.sh and set TELEGRAM_CHANNEL_ID"
    echo ""
    echo "Get your channel ID by visiting:"
    echo "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates"
    echo ""
    echo "Look for the negative number like: -1001234567890"
    echo "Then edit this file and replace YOUR_CHANNEL_ID_HERE"
    echo ""
    exit 1
fi

echo "✅ Configuration looks good!"
echo ""
echo "Bot Token: ${TELEGRAM_BOT_TOKEN:0:20}..."
echo "Channel ID: $TELEGRAM_CHANNEL_ID"
echo ""
echo "Starting signal bot..."
echo ""

# Run the bot
python3.11 telegram_bot.py

echo ""
echo "✅ Done! Check your Telegram channel for signals."
