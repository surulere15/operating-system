# PRD — Automation SaaS Platform + Marketplace (50 SKUs as Packages)

## 0) Summary
We are building a **multi-tenant automation platform** with a **marketplace storefront** where “products” are **automation SKUs** shipped as **packages** (templates/modules). The platform executes workflows (manual/scheduled), stores artifacts, and generates reports.

**Launch goal (14 days):** platform MVP + **10 SKUs live** with a clear path to immediate revenue via concierge-to-hosted conversion.

---

## 1) Problem
B2B teams lose time/money due to manual, document-heavy, compliance-heavy workflows:
- vendor security questionnaires (SIG/CAIQ)
- SOC2 evidence collection
- access reviews
- DSAR fulfillment
- contract renewal traps
- payment reconciliations
- chargeback evidence packaging
- collections/dunning
- compliance deadline tracking
- deal desk approvals

Existing tools are either:
- heavy enterprise suites (long implementation), or
- point solutions that don’t match SMB/midmarket speed and budget needs.

---

## 2) Goals & Non-Goals

### Goals
1. **Sell outcomes, not software**: customer pays, uploads/connects minimal inputs, gets an artifact within 24–48h.
2. **Single platform, many SKUs**: 10 SKUs in 14 days; 50 SKUs in 12 weeks.
3. **Low onboarding friction**: start with CSV/PDF upload and minimal connectors; add OAuth later.
4. **Auditability**: every run must have job logs, timestamps, and exportable evidence.

### Non-Goals (MVP)
- Full no-code builder for end-users
- Complex OAuth ecosystems for every app
- Real-time streaming/event processing
- SSO/SAML

---

## 3) Users & Personas

### Persona A — Ops/Finance/Procurement (SMB–midmarket)
- Wants renewal calendar, recon reports, collections automation
- Buys fast if deliverables are clear and setup is minimal

### Persona B — Security/GRC
- Needs evidence + audit trails
- Will pay more but expects credibility and data handling hygiene

### Persona C — RevOps/Sales Ops
- Wants standardized approvals, discount guardrails, deal logs

---

## 4) Product Offering

### Platform Components
1. **Workspace** (org + projects)
2. **Connectors** (API key / webhook / CSV / email)
3. **Workflow Runner** (manual + scheduled)
4. **Artifacts** (reports, CSVs, evidence packs)
5. **Audit Log** (who did what, when)
6. **Marketplace** (listing → purchase → activate)
7. **Billing/Licensing** (Stripe)

### SKU Concept
A SKU is a packaged automation that the platform can execute.

**SKU Package Files:**
- `inputs.schema.json`
- `workflow.yaml`
- `report.template.md`
- `pricing.json`
- `marketplace.md`

---

## 5) MVP Scope (Day 1–14)

### 5.1 Must-have features

#### Tenancy & Auth
- Email/password auth (or magic link)
- Org/workspace creation
- Basic RBAC: Admin, Member, Viewer

#### Marketplace
- SKU listing pages
- Purchase/subscribe via Stripe
- License gating (only run purchased SKUs)

#### Workflow Execution
- Run SKU manually (button)
- Schedule runs (cron)
- Queue + retries (basic)
- Job logs (step-level)

#### Inputs
- File upload (PDF/CSV/ZIP)
- Connector secrets storage (API keys)

#### Outputs
- Artifact storage per run
- Download reports (PDF/CSV)
- Email delivery (optional)

#### Auditing
- Immutable run history
- Who/when/inputs hash/outputs hash

### 5.2 Should-have features
- Slack notifications
- Webhook triggers
- Template “setup wizard” per SKU

### 5.3 Out of scope (MVP)
- End-user workflow designer
- Advanced branching UI
- SSO/SAML
- Deep app marketplaces

---

## 6) Initial 10 SKUs (Launch Pack)

**Tier A (fastest to paid):**
1. SKU05 Contract Renewal Trap Detector
2. SKU06 Stripe Reconciliation
3. SKU07 Chargeback Evidence Packager
4. SKU01 Security Questionnaire Autoresponder

**Tier B (high-ticket/heavier onboarding):**
5. SKU02 SOC2/ISO Evidence Collector
6. SKU03 SaaS Access Review Automation
7. SKU10 Deal Desk Autopilot
8. SKU09 Regulatory Deadline Sentinel
9. SKU04 DSAR Workflow
10. SKU08 Collections Autopilot

---

## 7) Key Workflows (User Journeys)

### Journey 1 — Buy & Run SKU
1. User visits marketplace listing
2. Purchases (one-time or subscription)
3. Creates workspace
4. Uploads required inputs / connects required tools
5. Runs SKU
6. Downloads report/artifact

### Journey 2 — Scheduled Runs
1. Admin sets schedule
2. Workflow runs automatically
3. Artifacts generated
4. User receives email/Slack notification

---

## 8) Functional Requirements

### FR-1: SKU Listing
- Render from `marketplace.md`
- Show deliverables, pricing, SLA, required inputs

### FR-2: Licensing
- Stripe customer → subscription/plan stored
- Gate run execution by active license

### FR-3: Execution Engine
- Steps: HTTP request, transform, file ingest, report render, notification
- Step-level logs
- Retry policy: 3 retries for transient errors

### FR-4: Artifact Store
- Store: input files, derived tables, final report
- Each artifact has checksum + timestamp

### FR-5: Audit Trail
- Every run stores: actor, SKU version, inputs hash, outputs hash, timestamps

---

## 9) Non-Functional Requirements
- Security: encrypted secrets, least privilege
- Reliability: idempotent runs where possible
- Performance: handle SMB scale (10–100 runs/day early)
- Privacy: PII-safe defaults; retention configurable later

---

## 10) Data Model (MVP)
- `User {id, email, role}`
- `Org {id, name}`
- `Workspace {id, orgId, name}`
- `SKU {id, slug, version, metadata}`
- `License {id, orgId, skuSlug, plan, status, stripeCustomerId}`
- `Run {id, skuSlug, workspaceId, actorId, status, startedAt, endedAt, inputsHash, outputsHash}`
- `RunStep {id, runId, name, status, startedAt, endedAt, logs}`
- `Artifact {id, runId, kind, path, checksum, createdAt}`
- `Secret {id, workspaceId, connector, encryptedBlob}`

---

## 11) Success Metrics
- Time-to-first-value: < 24h (concierge) and < 60 min (hosted) by week 4
- Paid conversion rate per SKU
- Attach rate to monthly plan after first one-time delivery
- Delivery hours per customer trending down

---

## 12) Risks & Mitigations
- **Risk:** Too many SKUs → quality collapse
  - Mitigation: strict SKU package spec + tiered rollout
- **Risk:** Integration complexity
  - Mitigation: CSV/PDF first, connectors later
- **Risk:** Trust barrier for compliance/security buyers
  - Mitigation: audit logs, clear data handling policy, concierge onboarding

---

## 13) Milestones
- Day 2: sales plumbing complete
- Day 7: platform MVP + SKU05 hosted
- Day 14: 10 SKUs live + marketplace buy/run flow
- Week 6: 25 SKUs
- Week 12: 50 SKUs
