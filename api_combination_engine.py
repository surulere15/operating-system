import random
import json

class APICombinationEngine:
    def __init__(self, api_list_path):
        self.api_list_path = api_list_path
        self.categories = {}
        self.load_apis()

    def load_apis(self):
        current_category = None
        try:
            with open(self.api_list_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('## '):
                        current_category = line.replace('## ', '').split(' (')[0]
                        self.categories[current_category] = []
                    elif line and (line[0].isdigit() or line.startswith('- ')):
                        # Simple parsing: assume "Number. Name - Description"
                        parts = line.split('. ', 1)
                        if len(parts) > 1:
                            api_info = parts[1].split(' - ', 1)
                            name = api_info[0]
                            desc = api_info[1] if len(api_info) > 1 else ""
                            if current_category:
                                self.categories[current_category].append({"name": name, "description": desc})
        except Exception as e:
            print(f"Error loading APIs: {e}")

    def generate_arbitrage_patterns(self):
        patterns = [
            {
                "name": "The Storm Chaser (Lead Gen)",
                "logic": "Combines environmental monitoring with outreach to high-ticket contractors.",
                "apis": ["Weather & Environment", "Government & Public Sector", "Development & Utility Tools"],
                "example": "NOAA (Storm Events) + US Patent & Trademark (Contractors) + Hunter.io (Direct Contact)"
            },
            {
                "name": "The School District Arbitrage (Real Estate)",
                "logic": "Maps high-value public services to property data for localized demand reports.",
                "apis": ["Government & Public Sector", "Data, Maps & Geolocation", "News, Content & Social"],
                "example": "Art Institute of Chicago (Cultural Density) + Zippopotam.us (Geo Boundaries) + Yelp Fusion (Local Amenities)"
            },
            {
                "name": "The DeAI Compute Broker (Web3)",
                "logic": "Pairs real-time compute pricing with regulatory shifts to find underpriced infra.",
                "apis": ["AI & Machine Learning", "Finance & Cryptocurrency", "Government & Public Sector"],
                "example": "Hugging Face (Model Demand) + Binance API (Token Liquidity) + EU AI Act (Regulatory Latency)"
            },
            {
                "name": "The Supply Chain Oracle (E-commerce)",
                "logic": "Predicts inventory shortages by pairing logistics data with global news events.",
                "apis": ["News, Content & Social", "Data, Maps & Geolocation", "Development & Utility Tools"],
                "example": "GNews (Port Strikes) + Marine Traffic (Tides API) + MailerLite (Email Alerts)"
            }
        ]
        return patterns

    def discover_random_combination(self):
        cat_names = list(self.categories.keys())
        if len(cat_names) < 2: return "Insufficient categories."
        
        c1, c2 = random.sample(cat_names, 2)
        api1 = random.choice(self.categories[c1])
        api2 = random.choice(self.categories[c2])
        
        return {
            "title": f"The {api1['name']} + {api2['name']} Synergy",
            "combination": [api1['name'], api2['name']],
            "hypothesis": f"Using {c1} data to optimize {c2} workflows."
        }

if __name__ == "__main__":
    engine = APICombinationEngine("/Users/sam/.openclaw/workspace/active_free_apis.txt")
    print("\n--- PROVEN ARBITRAGE PATTERNS ---")
    for pattern in engine.generate_arbitrage_patterns():
        print(f"Pattern: {pattern['name']}")
        print(f"Logic: {pattern['logic']}")
        print(f"Example: {pattern['example']}\n")
    
    print("--- RANDOM SYNERGY EXPERIMENT ---")
    combo = engine.discover_random_combination()
    print(combo)
