import time
import random
import json
from decimal import Decimal

# Simulation Constraints
SIM_DURATION_BLOCKS = 10
BLOCK_TIME_SEC = 1 # Accelerated for simulation
START_PRICE_ETH = 2600.0
CRASH_MAGNITUDE = 0.30 # -30%

# Mock Data
AAVE_POSITIONS = []
CURVE_POOLS = {}

def init_world():
    print("[*] Initializing World State (February 8, 2026)...")
    
    # generate mock aave positions
    for i in range(50):
        collateral_eth = random.uniform(10, 1000)
        debt_usdc = (collateral_eth * START_PRICE_ETH) * random.uniform(0.6, 0.85) # LTV 60-85%
        AAVE_POSITIONS.append({
            "id": f"0xUser{i}",
            "collateral": collateral_eth,
            "debt": debt_usdc,
            "liquidation_threshold": 0.85
        })
        
    # generate mock curve pool (stETH/ETH)
    CURVE_POOLS["stETH"] = {
        "eth_balance": 100000,
        "steth_balance": 100000,
        "A": 100 # Amplification coeff
    }
    print(f"[*] Generated {len(AAVE_POSITIONS)} Aave positions and Curve Pool.")

def check_aave_liquidations(current_price):
    liquidatable = []
    for pos in AAVE_POSITIONS:
        collateral_value = pos["collateral"] * current_price
        health_factor = collateral_value * pos["liquidation_threshold"] / pos["debt"]
        
        if health_factor < 1.0:
            liquidatable.append({
                "user": pos["id"],
                "hf": health_factor,
                "profit": (collateral_value * 0.05) # 5% liquidation bonus
            })
    return liquidatable

def check_curve_arb(current_price, panic_factor):
    # Simulate stETH de-peg as panic increases
    pool = CURVE_POOLS["stETH"]
    
    # Panic selling stETH for ETH
    sell_vol = random.uniform(100, 1000) * panic_factor
    pool["steth_balance"] += sell_vol
    pool["eth_balance"] -= sell_vol
    
    # Simple price impact formula
    ratio = pool["eth_balance"] / pool["steth_balance"]
    steth_price = current_price * ratio
    
    delta = current_price - steth_price
    if delta > (current_price * 0.02): # >2% depeg
        return {
            "type": "peg_arb",
            "delta": delta,
            "ratio": ratio,
            "profit_est": (100 * delta) # Arb 100 ETH worth
        }
    return None

def main():
    current_price = START_PRICE_ETH
    results = []
    
    try:
        for block in range(1, SIM_DURATION_BLOCKS + 1):
            # 1. Crash Price
            drop = random.uniform(0.02, 0.05) # Drop 2-5% per block
            current_price = current_price * (1 - drop)
            
            print(f"\n[Block {block}] ETH Price: ${current_price:.2f} ({((current_price/START_PRICE_ETH)-1)*100:.2f}%)")
            
            # 2. Check Liquidations
            liquidations = check_aave_liquidations(current_price)
            if liquidations:
                print(f"    🚨 LIQUIDATIONS: {len(liquidations)} users underwater!")
                for liq in liquidations:
                    print(f"       -> Target: {liq['user']} | HF: {liq['hf']:.3f} | Profit: ${liq['profit']:.2f}")
                    results.append({"block": block, "type": "liquidation", "data": liq})
            
            # 3. Check Curve Peg
            panic = block / SIM_DURATION_BLOCKS # Panic increases with time
            arb = check_curve_arb(current_price, panic * 5)
            if arb:
                print(f"    📉 PEG ALERT: stETH trading at {arb['ratio']:.3f} ETH")
                print(f"       -> Opportunity: ${arb['profit_est']:.2f} profit")
                results.append({"block": block, "type": "arb", "data": arb})
            
            time.sleep(BLOCK_TIME_SEC)
            
    except KeyboardInterrupt:
        pass
    
    # Save Report
    with open("vulnerability_log.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\n[*] Simulation Complete. Log saved to vulnerability_log.json")

if __name__ == "__main__":
    init_world()
    main()
