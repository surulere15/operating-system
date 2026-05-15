#!/bin/bash
# Telegram Notification Setup Script

echo "╔══════════════════════════════════════════════════════════╗"
echo "║       📱  TELEGRAM NOTIFICATION SETUP                    ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

echo "Step 1: Create Your Telegram Bot"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1. Open Telegram on your phone/desktop"
echo "2. Search for: @BotFather"
echo "3. Send: /newbot"
echo "4. Name your bot (e.g., 'My Trading Bot')"
echo "5. Set username (must end in '_bot', e.g., 'my_trading_bot_123')"
echo "6. Copy the token (looks like: 1234567890:ABCdef...)"
echo ""
read -p "📝 Enter your bot token: " BOT_TOKEN
echo ""

echo "Step 2: Get Your Chat ID"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1. In Telegram, search for: @userinfobot"
echo "2. Send: /start"
echo "3. Copy your ID (a number like: 123456789)"
echo ""
read -p "📝 Enter your chat ID: " CHAT_ID
echo ""

echo "Step 3: Testing Connection..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Test the connection
export TELEGRAM_BOT_TOKEN="$BOT_TOKEN"
export TELEGRAM_CHAT_ID="$CHAT_ID"

python3 telegram_notifier.py

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ SUCCESS! Telegram is configured!"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "To make this permanent, add to your ~/.bashrc or ~/.zshrc:"
    echo ""
    echo "export TELEGRAM_BOT_TOKEN='$BOT_TOKEN'"
    echo "export TELEGRAM_CHAT_ID='$CHAT_ID'"
    echo ""
    echo "Or run this command:"
    echo ""
    echo "echo \"export TELEGRAM_BOT_TOKEN='$BOT_TOKEN'\" >> ~/.bashrc"
    echo "echo \"export TELEGRAM_CHAT_ID='$CHAT_ID'\" >> ~/.bashrc"
    echo "source ~/.bashrc"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "🚀 Ready to launch bot with Telegram notifications!"
else
    echo ""
    echo "❌ Connection failed. Please check your token and chat ID."
fi
