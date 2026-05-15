# Automation SaaS + Marketplace — ROADMAP (50 SKUs as packages)

## North Star
Build **one automation platform** + **marketplace storefront**. Ship 50 “products” as **workflow packages** (templates/modules), not 50 standalone SaaS apps.

## Definition of a SKU (Package Spec)
Each SKU is a package with:
- `inputs.schema.json` — required data/integrations
- `workflow.yaml` — steps + branching
- `report.template.md` — report output
- `pricing.json` — plans + limits
- `marketplace.md` — listing copy + FAQs

## Phase 0 — Foundations (Day 0–2)
**Goal:** accept payment + deliver outcome (concierge acceptable).
- Offer definition + sample report + outreach scripts
- Payment links (Stripe)
- Intake form + upload

**Milestone:** first paid pilot can be accepted immediately.

## Phase 1 — MVP Platform (Day 3–7)
**Goal:** minimal platform runs workflows and produces reports.
- Auth + org/workspaces
- RBAC (Admin/Member/Viewer)
- Secrets vault (encrypted)
- Workflow runner (manual + scheduled)
- Job logs + audit trail
- Report export (PDF/CSV) + artifact store

**Marketplace MVP**
- SKU listing pages
- Purchase → activate (license gating)
- Run-now UI

**Milestone:** 1 SKU fully hosted end-to-end.

## Phase 2 — 10 SKU Launch Pack (Day 8–14)
**Goal:** 10 SKUs live; each produces a clear artifact.

### Tier A (fastest to paid)
1) SKU05 Contract Renewal Trap Detector
2) SKU06 Stripe Reconciliation
3) SKU07 Chargeback Evidence Packager
4) SKU01 Security Questionnaire Autoresponder

### Tier B (high-ticket; heavier onboarding)
5) SKU02 SOC2/ISO Evidence Collector
6) SKU03 SaaS Access Review Automation
7) SKU10 Deal Desk Autopilot
8) SKU09 Regulatory Deadline Sentinel
9) SKU04 DSAR Workflow
10) SKU08 Collections Autopilot

**Milestone:** marketplace has 10 purchasable SKUs + onboarding flows.

## Phase 3 — Scale to 25 SKUs (Weeks 3–6)
- Expand connectors (Google Workspace, M365, HubSpot, QuickBooks/Xero)
- SKU setup wizards
- Marketplace: categories/search/bundles/testimonials
- Ops tooling: workspace cloning, scheduling, support/SLA

**Milestone:** 25 SKUs, consistent packaging.

## Phase 4 — Scale to 50 SKUs (Weeks 7–12)
- Ship next 25 SKUs mostly as packages
- Partner channel: consultants/MSPs/agencies + referral tracking
- Enterprise features only if required (SSO/SAML, advanced RBAC)

**Milestone:** 50 SKUs live + repeatable GTM.

## Phase 5 — Moat & Optimization (Month 4+)
- SKU analytics (conversion, time-to-value)
- Knowledge base reuse across SKUs
- Vertical bundles (“Compliance Pack”, “Ecom Finance Pack”)
- Creator ecosystem (third-party templates)

## Metrics
- Time-to-first-value < 24h
- Paid conversion rate per SKU
- Attach rate to monthly plan after one-time delivery
- Delivery cost per SKU (hours)
