# 🏗️ GSTACK SPRINT PROTOCOL
## Joe's Native Sprint Methodology (Adapted from garrytan/gstack)

**Philosophy:** Think → Plan → Build → Review → Test → Ship → Reflect
**Source:** [garrytan/gstack](https://github.com/garrytan/gstack) (MIT License)

---

## Sprint Lifecycle

```
┌─────────────────────────────────────────────────────────────────┐
│  THINK      /office-hours     Reframe the problem               │
│  PLAN       /ceo-review       Find the 10-star product           │
│             /eng-review       Lock architecture & edge cases     │
│             /autoplan         Chain all reviews automatically    │
│  BUILD      /gsd-claw         Spec-driven execution              │
│  REVIEW     /security-audit   OWASP + STRIDE threat model        │
│  DEBUG      /investigate      Root-cause analysis (no guessing)  │
│  SHIP       /ship             Tests → push → PR → changelog      │
│  REFLECT    /retro            Weekly retrospective + metrics      │
└─────────────────────────────────────────────────────────────────┘
```

---

## Dispatch Routing

When Sam says something, Joe should route to the right skill:

| User Says | Skill to Invoke | Phase |
|-----------|-----------------|-------|
| "Let's think about X" / "What should I build?" | `/office-hours` | THINK |
| "Is this the right product?" / "Rethink this" | `/ceo-review` | PLAN |
| "Make it buildable" / "Architecture review" | `/eng-review` | PLAN |
| "Plan everything" / "Full review" | `/autoplan` | PLAN |
| "Let's build this" / "GSD mode" | `/gsd-claw` | BUILD |
| "Security audit" / "OWASP scan" | `/security-audit` | REVIEW |
| "Why is this broken?" / "Debug this" | `/investigate` | DEBUG |
| "Ship it" / "Create PR" | `/ship` | SHIP |
| "Weekly review" / "What did we ship?" | `/retro` | REFLECT |

### Complexity Routing

| Complexity | Route |
|------------|-------|
| One-liner fix, typo, config change | Just do it — no methodology needed |
| Multi-file feature, clear approach | Run `/eng-review` first, then build |
| Full product feature or project | Run `/autoplan` (chains CEO → Eng review) |
| New product or major pivot | Start with `/office-hours` |
| Post-incident / something broke | Start with `/investigate` |

---

## Integration with Joe's Departments

| Department | Primary gstack Skills |
|------------|----------------------|
| **DATA** | `/eng-review`, `/investigate` |
| **INNOVATION** | `/office-hours`, `/ceo-review`, `/autoplan` |
| **LEVERAGE** | `/ship`, `/autoplan` |
| **HUSTLE** | `/ceo-review`, `/office-hours` |
| **BRANDING** | `/ceo-review` (product positioning) |
| **VISIBILITY** | `/ship` (release notes, changelog) |
| **SURVIVAL** | `/security-audit`, `/investigate` |

---

## The Iron Laws

1. **No code without a plan.** For anything non-trivial, run at least `/eng-review`.
2. **No fixes without investigation.** When debugging, use `/investigate` — don't guess and patch.
3. **No shipping without tests.** `/ship` audits coverage and bootstraps frameworks if needed.
4. **No product without reframing.** New products start with `/office-hours`.
5. **Reflect weekly.** Run `/retro` every Friday to track velocity and identify patterns.

---

## Quick Reference: Skill Chain Examples

### Building a New Product Feature
```
/office-hours → /ceo-review → /eng-review → /gsd-claw → /security-audit → /ship → /retro
```

### Investigating a Production Bug
```
/investigate → (fix) → /ship
```

### Weekly Planning Session
```
/retro (review last week) → /office-hours (plan next week) → /autoplan (review the plan)
```

### Security Hardening Sprint
```
/security-audit → /investigate (for each finding) → /ship
```

---

**Adapted from garrytan/gstack (MIT License).** Methodology credit: Garry Tan, Y Combinator.
