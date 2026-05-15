---
name: prospecting
version: 0.1.0
---
# Prospecting Workspace (OpenClaw)

This is a **lead list builder + enrichment workspace**.

## What it does
- Turns an ICP prompt into a **structured lead schema**
- Supports **provider adapters** (BYO data vendor): Apollo / People Data Labs / Clearbit / Crunchbase (stubs)
- Provides a **public-web fallback** that builds *company lists* (domains + metadata) without claiming “verified emails/phones”
- Exports **CSV/JSON** to `~/ .openclaw/workspace/leads/`

## Non-goals (by default)
- No fabrication of emails/phones.
- No scraping behind logins (LinkedIn) unless you explicitly add an authorized connector.

## Quick start

### 1) Create a prospecting job
```bash
python3 /Users/sam/.openclaw/workspace/skills/prospecting/scripts/prospect.py \
  --name "uk_saas_founders_n8n" \
  --prompt "Find UK SaaS founders using n8n" \
  --limit 50
```

Outputs:
- `leads/uk_saas_founders_n8n/leads.csv`
- `leads/uk_saas_founders_n8n/leads.json`
- `leads/uk_saas_founders_n8n/job.json`

### 2) Enrich an existing list
```bash
python3 /Users/sam/.openclaw/workspace/skills/prospecting/scripts/enrich.py \
  --in leads/uk_saas_founders_n8n/leads.csv \
  --out leads/uk_saas_founders_n8n/leads.enriched.csv
```

## Environment variables (optional)
- `CLEARBIT_API_KEY` (company enrichment)
- `PDL_API_KEY` (people enrichment)
- `APOLLO_API_KEY` (people/company)

If no keys are set, the system still produces useful **company-level** lead lists.
