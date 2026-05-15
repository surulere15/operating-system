#!/bin/bash
# Sovereign Deployment Automator

echo "=== SOVEREIGN DEPLOYMENT START ==="

# 1. Check Docker Runtime
# Add Docker bundle to PATH as fallback
export PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH"

if ! command -v docker &> /dev/null
then
    echo "[!] ERROR: Docker not found. Please install Docker Desktop first."
    exit 1
fi

if ! docker info &> /dev/null
then
    echo "[!] ERROR: Docker daemon not running. Please launch Docker Desktop."
    exit 1
fi

echo "[✅] Docker Engine Detected."

# 2. Synchronize Secrets
echo "[*] Verifying .env credentials..."
if grep -q "RPC_URL=https" .env && grep -q "PRIVATE_KEY=[0-9a-f]" .env; then
    echo "[✅] Mainnet Credentials Verified."
else
    echo "[!] ERROR: .env is missing critical RPC or Wallet keys."
    exit 1
fi

# 3. Build & Launch Fleet
echo "[*] Building Sovereign Fleet Containers..."
docker-compose build

echo "[*] Launching Fleet in Detached Mode..."
docker-compose up -d

# 4. Final Status
echo "\n=== DEPLOYMENT SUCCESSFUL ==="
echo "The Sovereign Empire is now containerized and live."
echo "Use 'docker-compose logs -f' to monitor the swarm."
echo "Check sovereign_dashboard.py for real-time stats."
