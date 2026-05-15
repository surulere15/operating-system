# Alignment Governance System (AGS)

**Core Principle:** Every product decision must reinforce at least one of the three North Stars:
- **Safety** — the user feels understood and respected
- **Competence** — the user experiences measurable growth
- **Belonging** — the user feels continuity and a reason to return

**Ship rule:** If a decision supports none → it does not ship.

---

## 1) Governance Layer — The Alignment Gate

Every spec/PR/design review/prompt update must include these statements:

### A. Safety Statement
How does this reduce shame, confusion, or emotional risk?

Examples:
- Clear recovery paths after failure
- Non-judgmental language
- Private correction instead of public exposure

### B. Competence Statement
What measurable growth does this create?

Examples:
- Skill progression
- Reduced time-to-success
- Better decision quality

### C. Belonging Statement
Why will the user return?

Examples:
- Resume state
- Narrative continuity
- Persistent progress memory

**Enforcement:** If Safety + Competence + Belonging = 0 → **BLOCK**.

---

## 2) Execution Layer — North Star Tagging

Every work item must include at least one:
- `NS_SAFETY`
- `NS_COMPETENCE`
- `NS_BELONGING`

**No tag → no ticket → no work.**

---

## 3) Measurement Layer — Drift Alarms

### Safety Metrics (early warning)
- Rage taps
- Rapid back navigation
- Abandon immediately after error
- Correction-screen drop rate

### Competence Metrics (growth)
- Mastery progress / week
- Reduced time-to-success
- Increased difficulty tolerance
- Completion improvement trend

### Belonging Metrics (continuity)
- “Continue Adventure” click rate
- Return within 24h / 7d
- Session resume usage
- Streak continuation

**Triangle Health Rule:** Never optimize a single pillar alone.

---

## 4) Alignment Review Layer (Human Override)

Output:
- PASS / FAIL
- Violated pillar(s)
- Minimal rewrite required

Questions:
- **Safety:** Could this make a user feel stupid/exposed?
- **Competence:** Can we observe growth objectively?
- **Belonging:** Does this create a future reason to return?

---

## 5) Alignment Debt

When a release weakens alignment:
- Record debt, e.g. `-1 Safety`
- **Debt must be repaid within 2 sprints**.

---

## 6) System Integration

### Product Spec Template (required fields)
- Feature:
- Alignment Tags:
- Safety Statement:
- Competence Statement:
- Belonging Statement:
- Metrics Impact:

### PR Template (required checkboxes)
- [ ] Alignment statements included
- [ ] North Star tags assigned
- [ ] Metrics impact defined

### Analytics Dashboard (3 panels)
- Safety Health
- Competence Growth
- Belonging Continuity

---

## 7) Operating Rules
- Alignment > Features
- Emotional outcomes > UI polish
- Growth > engagement hacks
- Continuity > novelty
