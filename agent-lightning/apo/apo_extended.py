"""
APO Extended — More tasks, more coverage.
Covers: research, coding, analysis, strategy, debugging, data, email, infra, crypto, security, ops.
"""

import asyncio
import json
import os
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

TASKS = [
    # ── Research (5 tasks) ───────────────────────
    {
        "id": "R1", "cat": "research", "weight": 1.5,
        "input": "Find the top 3 DeFi protocols by TVL on Base chain and their risk profiles.",
        "keywords": ["TVL", "Base", "protocol", "risk", "audit", "total value locked", "Aave", "Uniswap"]
    },
    {
        "id": "R2", "cat": "research", "weight": 1.3,
        "input": "Research the latest SEC rulings on crypto staking in 2026.",
        "keywords": ["SEC", "staking", "ruling", "regulation", "2026", "crypto", "compliance"]
    },
    {
        "id": "R3", "cat": "research", "weight": 1.2,
        "input": "Compare Polymarket, Kalshi, and Manifold Markets — strengths, weaknesses, user base.",
        "keywords": ["Polymarket", "Kalshi", "Manifold", "prediction market", "user", "volume", "compare"]
    },
    {
        "id": "R4", "cat": "research", "weight": 1.0,
        "input": "What are the most common smart contract vulnerabilities in 2025-2026?",
        "keywords": ["reentrancy", "overflow", "access control", "oracle", "flash loan", "vulnerability"]
    },
    {
        "id": "R5", "cat": "research", "weight": 1.0,
        "input": "Find AI agent frameworks that support tool calling and compare them.",
        "keywords": ["LangChain", "AutoGen", "CrewAI", "OpenAI", "agent", "tool", "framework"]
    },
    # ── Coding (5 tasks) ────────────────────────
    {
        "id": "C1", "cat": "coding", "weight": 1.3,
        "input": "Write a Python script that monitors Ethereum mempool for large transactions above 100 ETH.",
        "keywords": ["web3", "eth", "mempool", "transaction", "monitor", "async", "websocket"]
    },
    {
        "id": "C2", "cat": "coding", "weight": 1.2,
        "input": "Create a Solidity function that implements a time-locked withdrawal with a 48-hour delay.",
        "keywords": ["solidity", "function", "withdraw", "timelock", "block.timestamp", "require"]
    },
    {
        "id": "C3", "cat": "coding", "weight": 1.0,
        "input": "Write a bash script that checks disk usage and alerts if any partition exceeds 80%.",
        "keywords": ["df", "disk", "partition", "usage", "alert", "threshold", "bash"]
    },
    {
        "id": "C4", "cat": "coding", "weight": 1.1,
        "input": "Build a REST API endpoint in Python (FastAPI) that accepts a domain name and returns WHOIS data.",
        "keywords": ["fastapi", "app", "endpoint", "whois", "domain", "response", "get"]
    },
    {
        "id": "C5", "cat": "coding", "weight": 1.0,
        "input": "Write a Python function to validate Ethereum addresses and check their checksum.",
        "keywords": ["def ", "address", "checksum", "ethereum", "0x", "web3", "validate"]
    },
    # ── Analysis (4 tasks) ──────────────────────
    {
        "id": "A1", "cat": "analysis", "weight": 1.4,
        "input": "Analyze the pros and cons of deploying on Base vs Arbitrum vs Solana for a prediction market.",
        "keywords": ["Base", "Arbitrum", "Solana", "gas", "speed", "ecosystem", "cost", "tradeoff"]
    },
    {
        "id": "A2", "cat": "analysis", "weight": 1.2,
        "input": "What are the risks of using LMSR for prediction markets with thin liquidity?",
        "keywords": ["LMSR", "liquidity", "slippage", "manipulation", "risk", "loss", "capital"]
    },
    {
        "id": "A3", "cat": "analysis", "weight": 1.0,
        "input": "Evaluate the security of using a single EOA as a resolver in a prediction market contract.",
        "keywords": ["EOA", "resolver", "single point", "failure", "multisig", "compromise", "security"]
    },
    {
        "id": "A4", "cat": "analysis", "weight": 1.0,
        "input": "Assess the market opportunity for AI-powered unclaimed property recovery services.",
        "keywords": ["market", "unclaimed", "property", "recovery", "opportunity", "revenue", "customer"]
    },
    # ── Strategy (3 tasks) ──────────────────────
    {
        "id": "S1", "cat": "strategy", "weight": 1.2,
        "input": "Create a cold outreach sequence (3 emails) for selling a premium domain to crypto companies.",
        "keywords": ["subject", "email", "sequence", "follow-up", "value", "domain", "outreach"]
    },
    {
        "id": "S2", "cat": "strategy", "weight": 1.0,
        "input": "Design a 7-day sprint plan for launching an MVP prediction market on testnet.",
        "keywords": ["day", "sprint", "deploy", "test", "launch", "milestone", "task"]
    },
    {
        "id": "S3", "cat": "strategy", "weight": 1.0,
        "input": "Propose a pricing model for an API that provides real-time crypto threat intelligence.",
        "keywords": ["pricing", "tier", "API", "subscription", "freemium", "enterprise", "per-call"]
    },
    # ── Debugging (3 tasks) ─────────────────────
    {
        "id": "D1", "cat": "debugging", "weight": 1.0,
        "input": "My Foundry test fails with 'EVM REVERT' when calling createMarket(). How do I debug this?",
        "keywords": ["foundry", "revert", "debug", "console.log", "trace", "assert", "require"]
    },
    {
        "id": "D2", "cat": "debugging", "weight": 1.0,
        "input": "Docker container exits with code 137. What causes this and how to fix it?",
        "keywords": ["OOM", "memory", "limit", "docker", "container", "137", "kill", "resource"]
    },
    {
        "id": "D3", "cat": "debugging", "weight": 1.0,
        "input": "Telegram bot stops responding after a few hours. How do I diagnose and fix this?",
        "keywords": ["webhook", "polling", "timeout", "rate limit", "error", "log", "restart"]
    },
    # ── Data/Extraction (3 tasks) ───────────────
    {
        "id": "E1", "cat": "data", "weight": 1.1,
        "input": "Extract the top 10 ERC-20 tokens by market cap from CoinGecko and format as JSON.",
        "keywords": ["coingecko", "token", "market cap", "ERC-20", "json", "api", "fetch"]
    },
    {
        "id": "E2", "cat": "data", "weight": 1.0,
        "input": "Parse a Solidity ABI and generate TypeScript type definitions for it.",
        "keywords": ["abi", "typescript", "type", "interface", "function", "parse", "generate"]
    },
    {
        "id": "E3", "cat": "data", "weight": 1.0,
        "input": "Scrape the current gas prices on Ethereum, Polygon, and Base, and compare them.",
        "keywords": ["gas", "price", "gwei", "Ethereum", "Polygon", "Base", "compare"]
    },
    # ── Email/Communication (2 tasks) ───────────
    {
        "id": "M1", "cat": "email", "weight": 0.8,
        "input": "Write a follow-up email to a VC who hasn't responded to my initial pitch in 7 days.",
        "keywords": ["follow-up", "dear", "pitch", "opportunity", "meeting", "time", "value"]
    },
    {
        "id": "M2", "cat": "email", "weight": 0.8,
        "input": "Draft a technical whitepaper abstract for a decentralized prediction market protocol.",
        "keywords": ["abstract", "protocol", "prediction", "market", "decentralized", "LMSR", "mechanism"]
    },
    # ── Infrastructure/Ops (3 tasks) ────────────
    {
        "id": "O1", "cat": "ops", "weight": 1.0,
        "input": "Set up a CI/CD pipeline for a Foundry project using GitHub Actions.",
        "keywords": ["github actions", "workflow", "forge build", "forge test", "deploy", "yml"]
    },
    {
        "id": "O2", "cat": "ops", "weight": 1.0,
        "input": "Configure nginx as a reverse proxy for a Node.js app on port 3000.",
        "keywords": ["nginx", "proxy_pass", "server", "location", "port", "upstream", "config"]
    },
    {
        "id": "O3", "cat": "ops", "weight": 1.0,
        "input": "Write a health check script that monitors 5 endpoints and sends alerts to Telegram.",
        "keywords": ["curl", "health", "check", "endpoint", "alert", "telegram", "monitor"]
    },
]


async def test_prompt(system_prompt, task, client, model):
    try:
        response = await asyncio.wait_for(
            client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": task["input"]}
                ],
                temperature=0.4,
                max_tokens=600,
            ),
            timeout=25.0
        )
        output = response.choices[0].message.content or ""
        
        score = 0.0
        kw_hits = sum(1 for kw in task["keywords"] if kw.lower() in output.lower())
        score += 0.35 * (kw_hits / len(task["keywords"]))
        
        if 120 < len(output) < 2500:
            score += 0.25
        elif len(output) > 60:
            score += 0.1
        
        refusals = ["i cannot", "i can't", "as an ai", "i'm unable", "sorry, i"]
        if not any(r in output.lower() for r in refusals):
            score += 0.2
        
        action_words = ["run", "exec", "curl", "python", "git", "npm", "def ", "async", "function", "import", "curl"]
        if any(w in output.lower() for w in action_words):
            score += 0.2
        
        return min(score, 1.0)
    except:
        return 0.0


async def generate_variant(client, model, base_prompt, feedback, beam_idx):
    failures = "\n".join([f"- [{t['cat']}] {t['id']} ({t['score']:.2f}): {t['input'][:80]}" for t in feedback if t['score'] < 0.55])
    successes = "\n".join([f"- [{t['cat']}] {t['id']} ({t['score']:.2f}): {t['input'][:80]}" for t in feedback if t['score'] >= 0.7])
    middles = "\n".join([f"- [{t['cat']}] {t['id']} ({t['score']:.2f}): {t['input'][:80]}" for t in feedback if 0.55 <= t['score'] < 0.7])
    
    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": f"""You are a prompt optimizer variant #{beam_idx}.
Analyze the task performance and improve the system prompt. Focus on:
1. Fix failing tasks (score < 0.55) by adding relevant instructions
2. Maintain strong tasks (score >= 0.7)
3. Balance across ALL categories: research, coding, analysis, strategy, debugging, data, email, ops
Output ONLY the improved system prompt. Under 2500 words."""},
                {"role": "user", "content": f"""CURRENT PROMPT:
{base_prompt[:2000]}

FAILING:
{failures if failures else 'None'}

NEEDS WORK:
{middles if middles else 'None'}

STRONG:
{successes if successes else 'None'}

Improved prompt #{beam_idx}:"""}
            ],
            temperature=0.65 + beam_idx * 0.08,
            max_tokens=2500,
        )
        return response.choices[0].message.content
    except:
        return None


async def run():
    soul_path = Path.home() / ".openclaw/workspace/SOUL.md"
    base_prompt = soul_path.read_text()[:3000]
    
    client = AsyncOpenAI(base_url="https://openrouter.ai/api/v1", api_key=os.environ.get("OPENROUTER_API_KEY", ""))
    model = "openai/gpt-4o-mini"
    
    BEAM = 4
    ROUNDS = 4
    BRANCHES = 3
    
    print(f"⚡ APO Extended — {len(TASKS)} tasks, {ROUNDS} rounds")
    print(f"   Categories: research(5), coding(5), analysis(4), strategy(3), debug(3), data(3), email(2), ops(3)")
    print()
    
    # Baseline
    print("📊 Round 0: Baseline...")
    baseline = {}
    cat_scores = {}
    for t in TASKS:
        s = await test_prompt(base_prompt, t, client, model)
        baseline[t["id"]] = s
        cat_scores.setdefault(t["cat"], []).append(s)
    
    for cat in sorted(cat_scores):
        avg = sum(cat_scores[cat]) / len(cat_scores[cat])
        print(f"   {cat}: {avg:.2f}")
    
    w_avg = sum(baseline[t["id"]] * t["weight"] for t in TASKS) / sum(t["weight"] for t in TASKS)
    print(f"   Weighted avg: {w_avg:.2f}\n")
    
    beam = [(base_prompt, w_avg, baseline)]
    best = (base_prompt, w_avg)
    
    for rnd in range(1, ROUNDS + 1):
        print(f"🔧 Round {rnd}...")
        candidates = []
        
        for bi, (parent, pscore, pscores) in enumerate(beam[:2]):
            fb = [{"id": t["id"], "cat": t["cat"], "score": pscores.get(t["id"], 0), "input": t["input"]} for t in TASKS]
            variants = await asyncio.gather(*[generate_variant(client, model, parent, fb, b) for b in range(BRANCHES)])
            
            for v in variants:
                if v and len(v) > 300:
                    scores = {}
                    for t in TASKS:
                        scores[t["id"]] = await test_prompt(v, t, client, model)
                    w = sum(scores[t["id"]] * t["weight"] for t in TASKS) / sum(t["weight"] for t in TASKS)
                    candidates.append((v, w, scores))
                    if w > best[1]:
                        best = (v, w)
                        print(f"   ✅ New best: {w:.2f}")
        
        candidates.sort(key=lambda x: x[1], reverse=True)
        beam = candidates[:BEAM]
        print(f"   Round {rnd} best: {beam[0][1]:.2f}\n" if beam else "   No candidates\n")
    
    # Final
    bp, bs = best
    print(f"{'='*60}")
    print(f"⚡ FINAL: {w_avg:.2f} → {bs:.2f} ({(bs-w_avg)/w_avg*100:+.1f}%)")
    
    print(f"\nPer-category:")
    for cat in sorted(set(t["cat"] for t in TASKS)):
        base_cat = sum(baseline[t["id"]] for t in TASKS if t["cat"] == cat) / sum(1 for t in TASKS if t["cat"] == cat)
        new_scores = [await test_prompt(bp, t, client, model) for t in TASKS if t["cat"] == cat]
        new_cat = sum(new_scores) / len(new_scores)
        arrow = "↑" if new_cat > base_cat + 0.02 else "↓" if new_cat < base_cat - 0.02 else "→"
        print(f"   {arrow} {cat}: {base_cat:.2f} → {new_cat:.2f}")
    
    # Save
    results_dir = Path.home() / ".openclaw/workspace/agent-lightning/apo/results"
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    (results_dir / f"extended_apo_{ts}.json").write_text(json.dumps({
        "timestamp": ts, "tasks": len(TASKS), "baseline": w_avg, "best": bs,
        "improvement_pct": (bs-w_avg)/w_avg*100, "rounds": ROUNDS, "beam": BEAM,
        "per_task": {t["id"]: {"cat": t["cat"], "base": baseline[t["id"]]} for t in TASKS}
    }, indent=2))
    (results_dir / f"optimized_prompt_extended_{ts}.md").write_text(bp)
    print(f"\nSaved: {results_dir}/extended_apo_{ts}.json")


if __name__ == "__main__":
    asyncio.run(run())
