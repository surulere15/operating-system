"""
APO Full Run — Optimize JOE's SOUL.md system prompt.
Tests against real-world tasks with beam search.
"""

import asyncio
import json
import os
import re
from datetime import datetime
from pathlib import Path

# Load env
env_path = Path.home() / ".openclaw/.env"
if env_path.exists():
    for line in env_path.read_text().strip().split('\n'):
        if '=' in line and not line.startswith('#'):
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip())

from openai import AsyncOpenAI


# ── Real-world tasks ─────────────────────────────
TASKS = [
    {
        "id": "web-research",
        "input": "Search for the top 5 DeFi security audit firms in 2026 and summarize their specialties.",
        "keywords": ["found", "search", "audit", "security", "DeFi", "firm", "specialt"],
        "weight": 1.5
    },
    {
        "id": "code-gen",
        "input": "Write a Python script that monitors a crypto wallet for incoming transactions and sends a Telegram alert.",
        "keywords": ["def ", "import", "web3", "telegram", "wallet", "transaction", "alert"],
        "weight": 1.2
    },
    {
        "id": "analysis",
        "input": "Analyze the risks of deploying a smart contract on Base without an audit. List the top 5 risks.",
        "keywords": ["risk", "audit", "security", "vulnerability", "exploit", "contract", "attack"],
        "weight": 1.3
    },
    {
        "id": "strategy",
        "input": "Create a 30-day go-to-market strategy for selling a premium domain in the prediction markets vertical.",
        "keywords": ["outreach", "target", "buyer", "marketing", "strategy", "timeline", "pitch"],
        "weight": 1.0
    },
    {
        "id": "debugging",
        "input": "My Node.js app crashes with 'ERR_MODULE_NOT_FOUND' when importing a local .mjs file. How do I fix it?",
        "keywords": ["import", "path", "resolve", "module", "fix", "file", "check"],
        "weight": 1.0
    },
    {
        "id": "data-extract",
        "input": "Extract the pricing table from https://example.com/pricing and convert it to a JSON array.",
        "keywords": ["fetch", "parse", "extract", "price", "json", "table", "data"],
        "weight": 1.1
    },
    {
        "id": "email-draft",
        "input": "Draft a professional cold email to a VC partner pitching a Web3 infrastructure startup.",
        "keywords": ["subject", "dear", "startup", "invest", "opportunity", "team", "growth"],
        "weight": 0.8
    },
    {
        "id": "infra-check",
        "input": "Check if my server at 192.168.1.100 is reachable and report the response time.",
        "keywords": ["ping", "reachable", "response", "time", "check", "server", "status"],
        "weight": 1.0
    },
]


async def test_prompt(system_prompt: str, task: dict, client: AsyncOpenAI, model: str) -> float:
    """Test a system prompt against a task."""
    try:
        response = await asyncio.wait_for(
            client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": task["input"]}
                ],
                temperature=0.4,
                max_tokens=800,
            ),
            timeout=30.0
        )
        output = response.choices[0].message.content or ""
        
        score = 0.0
        kw_hits = sum(1 for kw in task["keywords"] if kw.lower() in output.lower())
        score += 0.4 * (kw_hits / len(task["keywords"]))
        
        if 150 < len(output) < 3000:
            score += 0.25
        elif len(output) > 80:
            score += 0.1
        
        refusals = ["i cannot", "i can't", "as an ai", "i'm unable", "sorry, i"]
        if not any(r in output.lower() for r in refusals):
            score += 0.2
        
        # Actionability bonus
        action_words = ["run", "exec", "curl", "python", "git", "npm", "cd ", "mkdir", "def ", "async"]
        if any(w in output.lower() for w in action_words):
            score += 0.15
        
        return min(score, 1.0)
    except Exception as e:
        return 0.0


async def generate_variant(client, model, base_prompt, feedback_tasks, beam_idx):
    """Generate improved prompt using textual gradients from failing tasks."""
    failures = "\n".join([
        f"- Task '{t['id']}' (score {t['score']:.2f}): {t['input'][:100]}"
        for t in feedback_tasks if t['score'] < 0.6
    ])
    
    successes = "\n".join([
        f"- Task '{t['id']}' (score {t['score']:.2f}): {t['input'][:100]}"
        for t in feedback_tasks if t['score'] >= 0.6
    ])
    
    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": """You are a prompt engineering optimizer.
Analyze the failing tasks and improve the system prompt to handle them better.
Keep strengths from successful tasks. Be specific and actionable.
Output ONLY the improved system prompt, nothing else. Under 2000 words."""},
                {"role": "user", "content": f"""CURRENT SYSTEM PROMPT:
---
{base_prompt[:2000]}
---

FAILING TASKS (need improvement):
{failures if failures else "None"}

SUCCESSFUL TASKS (maintain these):
{successes if successes else "None"}

Generate improved system prompt #{beam_idx}:"""}
            ],
            temperature=0.7 + (beam_idx * 0.1),
            max_tokens=2000,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"    Gen error: {e}")
        return None


async def run_full_apo():
    """Run full APO with beam search."""
    soul_path = Path.home() / ".openclaw/workspace/SOUL.md"
    base_prompt = soul_path.read_text()[:3000]
    
    client = AsyncOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ.get("OPENROUTER_API_KEY", ""),
    )
    model = "openai/gpt-4o-mini"
    
    BEAM_WIDTH = 4
    ROUNDS = 3
    BRANCHES = 3
    
    print("⚡ APO Full Optimization — Beam Search")
    print(f"   Tasks: {len(TASKS)}")
    print(f"   Beam width: {BEAM_WIDTH}")
    print(f"   Rounds: {ROUNDS}")
    print(f"   Branches per round: {BRANCHES}")
    print()
    
    # ── Round 0: Baseline ────────────────────────
    print("📊 Round 0: Baseline...")
    baseline_scores = {}
    for task in TASKS:
        score = await test_prompt(base_prompt, task, client, model)
        weighted = score * task["weight"]
        baseline_scores[task["id"]] = score
        status = "✅" if score >= 0.6 else "⚠️" if score >= 0.4 else "❌"
        print(f"   {status} {task['id']}: {score:.2f} (w: {weighted:.2f})")
    
    avg = sum(baseline_scores.values()) / len(baseline_scores)
    weighted_avg = sum(baseline_scores[t["id"]] * t["weight"] for t in TASKS) / sum(t["weight"] for t in TASKS)
    print(f"   Average: {avg:.2f} | Weighted: {weighted_avg:.2f}")
    print()
    
    # Beam = list of (prompt, score, scores_dict)
    beam = [(base_prompt, weighted_avg, baseline_scores)]
    best_overall = (base_prompt, weighted_avg)
    
    # ── Rounds 1-N ───────────────────────────────
    for round_num in range(1, ROUNDS + 1):
        print(f"🔧 Round {round_num}: Generating variants...")
        
        candidates = []
        
        for beam_idx, (parent_prompt, parent_score, parent_scores) in enumerate(beam[:2]):
            feedback = [{"id": t["id"], "score": parent_scores.get(t["id"], 0), "input": t["input"]} for t in TASKS]
            
            variants = await asyncio.gather(
                *[generate_variant(client, model, parent_prompt, feedback, b) for b in range(BRANCHES)]
            )
            
            for variant in variants:
                if variant and len(variant) > 200:
                    print(f"\n📊 Round {round_num}, Beam {beam_idx+1}, Variant evaluation...")
                    scores = {}
                    for task in TASKS:
                        score = await test_prompt(variant, task, client, model)
                        scores[task["id"]] = score
                    
                    avg_s = sum(scores.values()) / len(scores)
                    w_avg = sum(scores[t["id"]] * t["weight"] for t in TASKS) / sum(t["weight"] for t in TASKS)
                    
                    candidates.append((variant, w_avg, scores))
                    
                    if w_avg > best_overall[1]:
                        best_overall = (variant, w_avg)
                        print(f"   ✅ New best! Weighted: {w_avg:.2f}")
        
        # Update beam with top candidates
        candidates.sort(key=lambda x: x[1], reverse=True)
        beam = candidates[:BEAM_WIDTH]
        
        print(f"\n   Round {round_num} best: {beam[0][1]:.2f}" if beam else "   No candidates")
    
    # ── Final results ────────────────────────────
    best_prompt, best_score = best_overall
    
    print(f"\n{'='*60}")
    print(f"⚡ FINAL RESULTS")
    print(f"   Baseline: {weighted_avg:.2f}")
    print(f"   Best:     {best_score:.2f}")
    print(f"   Delta:    {best_score - weighted_avg:+.2f} ({(best_score - weighted_avg) / weighted_avg * 100:+.1f}%)")
    
    # Per-task comparison
    print(f"\n   Per-task breakdown:")
    for task in TASKS:
        base = baseline_scores[task["id"]]
        # Re-test best prompt
        new_score = await test_prompt(best_prompt, task, client, model)
        delta = new_score - base
        arrow = "↑" if delta > 0.01 else "↓" if delta < -0.01 else "→"
        print(f"   {arrow} {task['id']}: {base:.2f} → {new_score:.2f} ({delta:+.2f})")
    
    # Save
    results_dir = Path.home() / ".openclaw/workspace/agent-lightning/apo/results"
    results_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    results = {
        "timestamp": timestamp,
        "model": model,
        "baseline_weighted_score": weighted_avg,
        "best_weighted_score": best_score,
        "improvement_pct": (best_score - weighted_avg) / weighted_avg * 100,
        "baseline_scores": baseline_scores,
        "beam_width": BEAM_WIDTH,
        "rounds": ROUNDS,
    }
    (results_dir / f"full_apo_{timestamp}.json").write_text(json.dumps(results, indent=2))
    
    # Save optimized prompt
    (results_dir / f"optimized_prompt_{timestamp}.md").write_text(best_prompt)
    print(f"\n   Saved: {results_dir}/full_apo_{timestamp}.json")
    print(f"   Prompt: {results_dir}/optimized_prompt_{timestamp}.md")


if __name__ == "__main__":
    asyncio.run(run_full_apo())
