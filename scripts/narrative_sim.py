import random
import time

class NegotiationSim:
    def __init__(self):
        self.alaba_score = 50 # Start neutral
        self.equity_offer = 15 # Starting equity offer (%)
        self.revenue_share = 5 # Starting rev share (%)
        
    def run_round(self, round_num, distributor_tactic):
        print(f"\\n[ROUND {round_num}] Distributor Tactic: {distributor_tactic}")
        
        # Alaba Response Logic (Based on Handbook)
        response = ""
        impact = 0
        
        if distributor_tactic == "Skepticism":
            response = '"We do not sell dreams. We sell logistics. Check the chain."'
            impact = 5
        elif distributor_tactic == "Price Pressure":
            response = '"Your margins are shrinking. Ours are zero-knowledge. Join or fade."'
            impact = 10
        elif distributor_tactic == "Regulatory FUD":
            response = '"Compliance is a feature of the old world. We are building the new one."'
            impact = -5 # Risky tactic
            
        print(f"    > Alaba Response: {response}")
        
        # Calculate Result
        roll = random.randint(1, 20) + impact
        if roll > 15:
            print("    [RESULT] DOMINANCE ESTABLISHED. (+Score)")
            self.alaba_score += 10
            self.equity_offer -= 1 # Stronger hand, lower offer
        else:
            print("    [RESULT] RESISTANCE ENCOUNTERED. (-Score)")
            self.alaba_score -= 5
            self.revenue_share += 0.5 # Weaken hand, higher rev share
            
    def conclude(self):
        print("=" * 40)
        print(f"FINAL SCORE: {self.alaba_score}")
        if self.alaba_score > 70:
            print("VERDICT: DEAL SECURED. TERMS: Dominant.")
            print(f"Final Terms: {self.equity_offer}% Equity / {self.revenue_share}% Rev Share")
            return "VICTORY"
        elif self.alaba_score > 40:
            print("VERDICT: DEAL SECURED. TERMS: Balanced.")
            print(f"Final Terms: {self.equity_offer}% Equity / {self.revenue_share}% Rev Share")
            return "SUCCESS"
        else:
            print("VERDICT: NEGOTIATION FAILED. WALK AWAY.")
            return "FAILURE"

def main():
    print("=== NARRATIVE WAR GAME: ALABAMARKET NEGOTIATION ===")
    sim = NegotiationSim()
    
    tactics = ["Skepticism", "Price Pressure", "Regulatory FUD", "Price Pressure", "Skepticism"]
    
    for i, tactic in enumerate(tactics):
        sim.run_round(i+1, tactic)
        time.sleep(0.5)
        
    result = sim.conclude()
    
    # Write Report
    with open("narrative_wargame_log.txt", "w") as f:
        f.write(f"Simulation Result: {result}\\nFinal Score: {sim.alaba_score}")

if __name__ == "__main__":
    main()
