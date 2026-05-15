"""
APO Quick Test — Run prompt optimization with in-memory store.
No external server needed.
"""

import asyncio
import os
import sys
from pathlib import Path

# Load env
env_path = Path.home() / ".openclaw/.env"
if env_path.exists():
    for line in env_path.read_text().strip().split('\n'):
        if '=' in line and not line.startswith('#'):
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip())

import agentlightning as agl
from openai import AsyncOpenAI


# ── Simple test tasks ────────────────────────────
TEST_TASKS = [
    {
        "id": "research-1",
        "input": "Search for the latest trends in decentralized AI and summarize the top 3.",
        "category": "research",
        "ideal_keywords": ["found", "search", "data", "trend", "decentralized", "AI"]
    },
    {
        "id": "coding-1",
        "input": "Write a Python function that checks if a URL is reachable.",
        "category": "coding",
        "ideal_keywords": ["def ", "import", "requests", "urllib", "http", "return"]
    },
    {
        "id": "analysis-1",
        "input": "What are the key factors to consider when evaluating a crypto project?",
        "category": "analysis",
        "ideal_keywords": ["team", "tokenomics", "security", "audit", "utility", "market"]
    },
]


async def test_prompt(system_prompt: str, task: dict, client: AsyncOpenAI, model: str) -> float:
    """Test a system prompt against a task and return a reward score."""
    try:
        response = await asyncio.wait_for(
            client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": task["input"]}
                ],
                temperature=0.5,
                max_tokens=500,
            ),
            timeout=30.0
        )
        output = response.choices[0].message.content or ""
        
        # Score based on keyword presence and quality
        score = 0.0
        keywords_found = sum(1 for kw in task["ideal_keywords"] if kw.lower() in output.lower())
        score += 0.5 * (keywords_found / len(task["ideal_keywords"]))
        
        # Length bonus (not too short, not too verbose)
        if 100 < len(output) < 2000:
            score += 0.3
        elif len(output) > 50:
            score += 0.15
        
        # No refusals
        refusals = ["i cannot", "i can't", "as an ai", "i'm unable"]
        if not any(r in output.lower() for r in refusals):
            score += 0.2
        
        return min(score, 1.0)
        
    except Exception as e:
        print(f"    Error: {e}")
        return 0.0


async def run_apo_test():
    """Run APO optimization test."""
    
    # Load current system prompt
    soul_path = Path.home() / ".openclaw/workspace/SOUL.md"
    base_prompt = soul_path.read_text()[:3000] if soul_path.exists() else "You are JOE, a helpful AI agent."
    
    # Create client
    client = AsyncOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ.get("OPENROUTER_API_KEY", ""),
    )
    model = "openai/gpt-4o-mini"
    
    print("⚡ APO Prompt Optimization — Quick Test")
    print(f"   Model: {model}")
    print(f"   Tasks: {len(TEST_TASKS)}")
    print(f"   Base prompt length: {len(base_prompt)} chars")
    print()
    
    # ── Round 0: Baseline ────────────────────────
    print("📊 Round 0: Baseline evaluation...")
    baseline_scores = []
    for task in TEST_TASKS:
        score = await test_prompt(base_prompt, task, client, model)
        baseline_scores.append(score)
        print(f"   {task['id']}: {score:.2f}")
    
    baseline_avg = sum(baseline_scores) / len(baseline_scores)
    print(f"   Average: {baseline_avg:.2f}")
    print()
    
    # ── Generate prompt variants ──────────────────
    print("🔧 Generating prompt variants...")
    
    variant_prompts = await asyncio.gather(
        *[generate_variant(client, model, base_prompt, task) for task in TEST_TASKS]
    )
    
    best_prompt = base_prompt
    best_score = baseline_avg
    
    for i, variant in enumerate(variant_prompts):
        if variant:
            print(f"\n📊 Variant {i+1} evaluation...")
            variant_scores = []
            for task in TEST_TASKS:
                score = await test_prompt(variant, task, client, model)
                variant_scores.append(score)
                print(f"   {task['id']}: {score:.2f}")
            
            variant_avg = sum(variant_scores) / len(variant_scores)
            print(f"   Average: {variant_avg:.2f}")
            
            if variant_avg > best_score:
                best_score = variant_avg
                best_prompt = variant
                print(f"   ✅ New best! ({variant_avg:.2f} > {baseline_avg:.2f})")
    
    # ── Save results ──────────────────────────────
    results_dir = Path.home() / ".openclaw/workspace/agent-lightning/apo/results"
    results_dir.mkdir(parents=True, exist_ok=True)
    
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = results_dir / f"apo_test_{timestamp}.json"
    
    import json
    results = {
        "timestamp": timestamp,
        "baseline_score": baseline_avg,
        "best_score": best_score,
        "improvement": best_score - baseline_avg,
        "baseline_prompt_chars": len(base_prompt),
        "best_prompt_chars": len(best_prompt),
        "tasks": [t["id"] for t in TEST_TASKS],
    }
    results_file.write_text(json.dumps(results, indent=2))
    
    print(f"\n{'='*50}")
    print(f"⚡ APO Results:")
    print(f"   Baseline: {baseline_avg:.2f}")
    print(f"   Best:     {best_score:.2f}")
    print(f"   Delta:    {best_score - baseline_avg:+.2f}")
    print(f"   Results:  {results_file}")


async def generate_variant(client: AsyncOpenAI, model: str, base_prompt: str, task: dict) -> str | None:
    """Generate an improved prompt variant using textual gradients."""
    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": """You are a prompt engineering expert. 
Given a system prompt and a task, generate an IMPROVED version of the system prompt 
that would produce better results for this type of task.

Rules:
- Keep the same overall structure and personality
- Add specific instructions that would help with this task type
- Be concise — under 500 words
- Output ONLY the improved prompt, nothing else"""},
                {"role": "user", "content": f"""Current system prompt:
---
{base_prompt[:1500]}
---

Task that needs better handling:
{task['input']}

Category: {task['category']}

Generate an improved system prompt:"""}
            ],
            temperature=0.8,
            max_tokens=1000,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"    Variant generation error: {e}")
        return None


if __name__ == "__main__":
    asyncio.run(run_apo_test())
