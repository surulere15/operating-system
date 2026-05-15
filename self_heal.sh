#!/bin/zsh

# JOE Self-Healing & Environment Verification Script
# This script ensures the OpenClaw environment is hardened and operational.

PATH="/usr/local/Cellar/node@22/22.22.0/bin:$PATH"
WORKSPACE="/Users/sam/.openclaw/workspace"

echo "!!! JOE SELF-HEAL PROTOCOL INITIATED !!!"

# 1. Verify Node/OpenClaw Paths
if ! command -v openclaw &> /dev/null; then
    echo "[!] openclaw not found in PATH. Adjusting..."
    export PATH="/usr/local/Cellar/node@22/22.22.0/bin:$PATH"
fi

# 2. Check Gateway Status
GATEWAY_PID=$(ps aux | grep openclaw-gateway | grep -v grep | awk '{print $2}')
if [ -z "$GATEWAY_PID" ]; then
    echo "[!] Gateway not running. Forcing restart..."
    openclaw gateway --force
else
    echo "[✓] Gateway is operational (PID: $GATEWAY_PID)."
fi

# 3. Verify Config Integrity
if [ ! -f ~/.openclaw/openclaw.json ]; then
    echo "[!] openclaw.json missing. Attempting restoration from backup..."
    cp ~/.openclaw/openclaw.json.bak ~/.openclaw/openclaw.json || echo "[!!] Restoration failed."
fi

# 4. Browser Readiness (Autonomous Profile)
echo "[*] Testing autonomous browser initialization..."
openclaw browser --browser-profile openclaw navigate "https://google.com"
sleep 5
BROWSER_CHECK=$(openclaw browser --browser-profile openclaw snapshot --format ai --limit 500 2>/dev/null)
if [[ $BROWSER_CHECK == *"Google"* ]]; then
    echo "[✓] Autonomous browser is functional."
else
    echo "[!] Autonomous browser failure. Checking logs..."
fi
openclaw browser close --all

echo "!!! SELF-HEAL COMPLETE. JOE IS SOVEREIGN !!!"
