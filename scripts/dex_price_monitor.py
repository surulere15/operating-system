import os
import sys
import time
from web3 import Web3

# Add local site-packages
sys.path.append(os.path.expanduser("~/Library/Python/3.9/lib/python/site-packages"))

# Config
RPC_URL = "https://eth.llamarpc.com"
WETH_ADDRESS = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
USDC_ADDRESS = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
AMOUNT_IN = 1 * 10**18 # 1 ETH

# Uniswap V3 Quoter V2 Address
UNI_QUOTER_ADDRESS = "0x61fFE0149A332c47d847290549742082b43d8479"

# Simplified ABIs
UNI_ABI = [
    {
        "inputs": [
            {
                "components": [
                    {"internalType": "address", "name": "tokenIn", "type": "address"},
                    {"internalType": "address", "name": "tokenOut", "type": "address"},
                    {"internalType": "uint24", "name": "fee", "type": "uint24"},
                    {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                    {"internalType": "uint160", "name": "sqrtPriceLimitX96", "type": "uint160"}
                ],
                "internalType": "struct IQuoterV2.QuoteExactInputSingleParams",
                "name": "params",
                "type": "tuple"
            }
        ],
        "name": "quoteExactInputSingle",
        "outputs": [
            {"internalType": "uint256", "name": "amountOut", "type": "uint256"},
            {"internalType": "uint160", "name": "sqrtPriceX96After", "type": "uint160"},
            {"internalType": "uint32", "name": "initializedTicksCrossed", "type": "uint32"},
            {"internalType": "uint256", "name": "gasEstimate", "type": "uint256"}
        ],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

# Uniswap V2 / SushiSwap Router
SUSHI_ROUTER_ADDRESS = "0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F"
SUSHI_ABI = [
    {
        "inputs": [
            {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
            {"internalType": "address[]", "name": "path", "type": "address[]"}
        ],
        "name": "getAmountsOut",
        "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}],
        "stateMutability": "view",
        "type": "function"
    }
]

def main():
    print(f"[*] Starting DEX Price Monitor (Quantum-Arb Perception)...")
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    if not w3.is_connected():
        print("[!] Failed to connect.")
        return

    uni_quoter = w3.eth.contract(address=Web3.to_checksum_address(UNI_QUOTER_ADDRESS), abi=UNI_ABI)
    sushi_router = w3.eth.contract(address=Web3.to_checksum_address(SUSHI_ROUTER_ADDRESS), abi=SUSHI_ABI)

    print(f"[*] Monitoring WETH -> USDC on UniV3 vs SushiSwap...")

    # Checksum token addresses
    weth_checksum = Web3.to_checksum_address(WETH_ADDRESS)
    usdc_checksum = Web3.to_checksum_address(USDC_ADDRESS)

    while True:
        try:
            # 1. Get Uniswap V3 Price (0.3% tier = 3000)
            # params: tokenIn, tokenOut, fee, amountIn, sqrtPriceLimitX96
            params = (weth_checksum, usdc_checksum, 3000, AMOUNT_IN, 0)
            uni_out = uni_quoter.functions.quoteExactInputSingle(params).call()
            uni_price = uni_out[0] / 10**6 # USDC has 6 decimals

            # 2. Get SushiSwap Price
            path = [weth_checksum, usdc_checksum]
            sushi_out = sushi_router.functions.getAmountsOut(AMOUNT_IN, path).call()
            sushi_price = sushi_out[1] / 10**6

            # 3. Calculate Delta
            diff = abs(uni_price - sushi_price)
            avg = (uni_price + sushi_price) / 2
            pct = (diff / avg) * 100

            print(f"[*] UniV3: ${uni_price:.2f} | Sushi: ${sushi_price:.2f} | Delta: {pct:.4f}%")

            if pct > 0.5:
                print(f"    🚨 ARBITRAGE OPPORTUNITY! Delta > 0.5%")
            
            time.sleep(3)

        except Exception as e:
            print(f"[!] Error: {e}")
            time.sleep(3)

if __name__ == "__main__":
    main()
