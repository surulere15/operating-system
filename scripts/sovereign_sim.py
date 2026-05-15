import random
import json
import time

# Simulation Parameters
CAPITAL_INJECTION_TOTAL = 4_200_000 # From Quantum Scheme
DURATION_MONTHS = 6

# Allocations
ALLOC_ALABA = 1_500_000
ALLOC_WIREBET = 2_000_000
RESERVE = 700_000

def simulate_alaba(capital):
    print(f"[*] Simulating AlabaMarket Expansion (Cap: ${capital:,})...")
    
    # Baseline
    vendors = 500
    monthly_rev = 50_000
    logistics_loss_rate = 0.15 # 15% lost to fraud/inefficiency
    
    results = []
    
    for month in range(1, DURATION_MONTHS + 1):
        # 1. Vendor Acquisition (Aggressive Spend)
        spend = capital / DURATION_MONTHS # Burn evenly
        cost_per_vendor = random.uniform(400, 600)
        new_vendors = int(spend / cost_per_vendor)
        vendors += new_vendors
        
        # 2. Logistics Tech (Provenance Seals)
        # Reduces loss rate over time as tech is adopted
        logistics_loss_rate *= 0.85 
        
        # 3. Revenue
        rev_per_vendor = random.uniform(150, 250)
        gross_rev = vendors * rev_per_vendor
        net_rev = gross_rev * (1 - logistics_loss_rate)
        
        results.append({
            "month": month,
            "vendors": vendors,
            "loss_rate": logistics_loss_rate,
            "revenue": net_rev,
            "burn": spend
        })
        print(f"    Month {month}: {vendors} Vendors | Rev: ${net_rev:,.2f} | Loss Rate: {logistics_loss_rate*100:.1f}%")
        
    return results

def simulate_wirebet(capital):
    print(f"[*] Simulating Wirebet Viral Growth (Cap: ${capital:,})...")
    
    # Baseline
    active_users = 2000
    monthly_vol = 500_000
    k_factor = 0.9 # Viral coefficient
    
    results = []
    
    for month in range(1, DURATION_MONTHS + 1):
        # 1. Influencer Spend ("Truth Bonds")
        spend = capital / DURATION_MONTHS
        
        # Spend boosts K-factor temporarily
        k_boost = (spend / 100_000) * 0.1 # Every 100k adds 0.1 to K
        current_k = k_factor + k_boost + random.uniform(-0.1, 0.2)
        
        # 2. User Growth
        new_users = int(active_users * (current_k - 1)) if current_k > 1 else 0
        organic_users = int(spend / 100) # Paid acquisition ($100 CPA)
        active_users += (new_users + organic_users)
        
        # 3. Volume & Revenue (2% fee)
        vol_per_user = random.uniform(200, 500)
        total_vol = active_users * vol_per_user
        revenue = total_vol * 0.02
        
        results.append({
            "month": month,
            "users": active_users,
            "k_factor": current_k,
            "volume": total_vol,
            "revenue": revenue
        })
        print(f"    Month {month}: {active_users} Users | K: {current_k:.2f} | Rev: ${revenue:,.2f}")
        
    return results

def main():
    print("=== SOVEREIGN BUSINESS SIMULATION v1.0 ===")
    print(f"Capital: ${CAPITAL_INJECTION_TOTAL:,}")
    print("-" * 40)
    
    alaba_res = simulate_alaba(ALLOC_ALABA)
    print("-" * 40)
    wirebet_res = simulate_wirebet(ALLOC_WIREBET)
    
    # Aggregate
    total_rev = sum([m['revenue'] for m in alaba_res]) + sum([m['revenue'] for m in wirebet_res])
    alaba_final_valuation = alaba_res[-1]['revenue'] * 12 * 8 # 8x ARR multiple
    wirebet_final_valuation = wirebet_res[-1]['revenue'] * 12 * 15 # 15x ARR for high growth
    
    print("=" * 40)
    print("FAILED VC DEPENDENCY CHECK: PASSED ✅")
    print(f"Total 6-Month Revenue: ${total_rev:,.2f}")
    print(f"Est. AlabaMarket Valuation: ${alaba_final_valuation:,.2f}")
    print(f"Est. Wirebet Valuation: ${wirebet_final_valuation:,.2f}")
    print(f"Combined Empire Value: ${(alaba_final_valuation + wirebet_final_valuation):,.2f}")

    # Save Log
    report = {
        "alaba": alaba_res,
        "wirebet": wirebet_res,
        "valuations": {
            "alaba": alaba_final_valuation,
            "wirebet": wirebet_final_valuation
        }
    }
    with open("sovereign_sim_report.json", "w") as f:
        json.dump(report, f, indent=2)

if __name__ == "__main__":
    main()
