import os
import sys
import time
from web3 import Web3
from decimal import Decimal
from dotenv import load_dotenv

# Add local site-packages to path just in case
sys.path.append(os.path.expanduser("~/Library/Python/3.9/lib/python/site-packages"))

# Load environment variables
load_dotenv()

# Configuration
RPC_URL = os.getenv("RPC_URL", "https://eth.llamarpc.com") 
WHALE_THRESHOLD_ETH = 10.0

def main():
    print(f"[*] Starting MEV Scanner (Flash-Scout Swarm)...")
    print(f"[*] Connecting to RPC: {RPC_URL}")
    
    try:
        w3 = Web3(Web3.HTTPProvider(RPC_URL))
        if not w3.is_connected():
            print("[!] Failed to connect to RPC.")
            return
        
        print(f"[*] Connected! Current Block: {w3.eth.block_number}")
        print(f"[*] Scanning for transactions > {WHALE_THRESHOLD_ETH} ETH...")
        
        # In a real MEV bot, we'd subscribe to 'pending_transactions' via WebSocket.
        # Over HTTP, we'll poll the latest block to demonstrate "Whale Watching".
        last_block = 0
        
        while True:
            try:
                current_block = w3.eth.block_number
                if current_block > last_block:
                    block = w3.eth.get_block(current_block, full_transactions=True)
                    print(f"\n[+] Processing Block #{current_block} with {len(block.transactions)} txs")
                    
                    found_whale = False
                    for tx in block.transactions:
                        # Value is in Wei, convert to ETH
                        value_eth = w3.from_wei(tx['value'], 'ether')
                        
                        if value_eth >= WHALE_THRESHOLD_ETH:
                            print(f"    🐋 WHALE ALERT: {value_eth:.2f} ETH | Hash: {tx['hash'].hex()}")
                            print(f"       From: {tx['from']} -> To: {tx['to']}")
                            found_whale = True
                            
                    if not found_whale:
                        print("    (No whale movements > 10 ETH in this block)")
                        
                    last_block = current_block
                
                time.sleep(2) # Poll every 2 seconds
                
            except Exception as e:
                print(f"[!] Error polling block: {e}")
                time.sleep(5)
                
    except KeyboardInterrupt:
        print("\n[*] Stopping Scanner...")

if __name__ == "__main__":
    main()
