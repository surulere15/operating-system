#!/usr/local/bin/python3
import pandas as pd
import os
import json

# Paths
LEADS_CSV = "/Users/sam/Downloads/wirebet_3k_plus_ceo_targets.csv"
WORKSPACE = "/Users/sam/.openclaw/workspace"
OUTPUT_DIR = os.path.join(WORKSPACE, "leads")

def process_leads():
    if not os.path.exists(LEADS_CSV):
        print(f"Error: {LEADS_CSV} not found.")
        return

    # Create output dir
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Load Data
    print(f"Loading leads from {LEADS_CSV}...")
    df = pd.read_csv(LEADS_CSV)

    # Print Summary
    print(f"Total leads found: {len(df)}")
    
    # Segment: Cluster Heads (Logic: Platform or Group in Category)
    cluster_heads = df[df['Category'].str.contains('Group|Platform|Groups|White-label', case=False, na=False)]
    
    # Segment: Crypto
    crypto_leads = df[df['Category'].str.contains('Crypto', case=False, na=False)]
    
    # Segment: Africa
    africa_leads = df[df['Region'].str.contains('Africa', case=False, na=False)]

    # Save Segments
    cluster_heads.to_csv(os.path.join(OUTPUT_DIR, "cluster_heads.csv"), index=False)
    crypto_leads.to_csv(os.path.join(OUTPUT_DIR, "crypto_leads.csv"), index=False)
    africa_leads.to_csv(os.path.join(OUTPUT_DIR, "africa_leads.csv"), index=False)

    print(f"--- Segmentation Complete ---")
    print(f"Cluster Heads: {len(cluster_heads)}")
    print(f"Crypto Leads: {len(crypto_leads)}")
    print(f"Africa Leads: {len(africa_leads)}")
    print(f"Files saved to: {OUTPUT_DIR}")

if __name__ == "__main__":
    process_leads()
