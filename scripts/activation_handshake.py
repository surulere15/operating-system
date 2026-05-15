#!/usr/bin/env python3
import os
import sys
from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv

# Path configuration
WORKSPACE_DIR = "/Users/sam/.openclaw/workspace"
ENV_PATH = os.path.join(WORKSPACE_DIR, ".env")

# Load environment
if os.path.exists(ENV_PATH):
    load_dotenv(ENV_PATH)
else:
    print(f"[!] .env not found at {ENV_PATH}")
    sys.exit(1)

RPC_URL = os.getenv("RPC_URL")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")

def handshake():
    print("=== SOVEREIGN ACTIVATION HANDSHAKE ===")
    
    if not RPC_URL or not PRIVATE_KEY:
        print("[!] Missing RPC_URL or PRIVATE_KEY in .env")
        return

    try:
        # 1. Connection Check
        w3 = Web3(Web3.HTTPProvider(RPC_URL))
        if not w3.is_connected():
            print("[!] Failed to connect to Ethereum Mainnet (Alchemy).")
            return
        
        block = w3.eth.block_number
        print(f"[✅] CONNECTED: Mainnet Block #{block}")

        # 2. Wallet Derivation
        # Remove 0x prefix if present for Account.from_key
        key = PRIVATE_KEY.strip()
        if key.startswith("0x"):
            key = key[2:]
            
        account = Account.from_key(key)
        address = account.address
        print(f"[✅] WALLET DERIVED: {address}")

        # 3. Balance Check
        balance_wei = w3.eth.get_balance(address)
        balance_eth = w3.from_wei(balance_wei, 'ether')
        print(f"[✅] BALANCE: {balance_eth:.4f} ETH")

        print("\n=== ACTIVATION SUCCESSFUL ===")
        print("The Sovereign Engine is now 'Hot'.")

    except Exception as e:
        print(f"[❌] ACTIVATION FAILED: {e}")

if __name__ == "__main__":
    handshake()
