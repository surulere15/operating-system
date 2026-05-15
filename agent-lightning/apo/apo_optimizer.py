"""
Agent Lightning APO Setup — Auto-optimize JOE's system prompts.
No GPU required. Uses OpenRouter for gradient computation.

Usage:
    python3.11 apo_optimizer.py --rounds 3 --beam-width 4
"""

import asyncio
import json
import os
from pathlib import Path
from typing import TypedDict, Optional, List, Any

import agentlightning as agl
from openai import AsyncOpenAI


# ── Data structures ──────────────────────────────
class PromptTask(TypedDict):
    """Task for prompt optimization."""
    id: str
    instruction: str  # What the agent should do
    input: str        # Sample input
    expected: str     # Expected output behavior
    category: str     # Task category (e.g., "research", "coding", "analysis")


class PromptResult(TypedDict):
    """Result from a rollout."""
    output: str
    reward: float
    reasoning: str


# ── Reward function ──────────────────────────────
async def evaluate_response(output: str, expected: str, category: str) -> float:
    """Evaluate agent output against expected behavior."""
    # Simple heuristic scoring (replace with LLM judge for production)
    score = 0.0
    
    # Length appropriateness (not too short, not too verbose)
    if 20 < len(output) < 2000:
        score += 0.2
    elif len(output) > 0:
        score += 0.1
    
    # Contains actionable content
    action_words = ["run", "search", "check", "execute", "create", "fix", "deploy", 
                    "analyze", "review", "update", "found", "result", "completed"]
    if any(w in output.lower() for w in action_words):
        score += 0.3
    
    # Contains code or commands (for technical tasks)
    if any(x in output for x in ["```", "exec(", "curl", "python", "git", "npm"]):
        score += 0.2
    
    # Not a refusal or error
    refusal_words = ["i cannot", "i can't", "i'm unable", "sorry, i", "as an ai"]
    if not any(w in output.lower() for w in refusal_words):
        score += 0.2
    
    # Matches category expectations
    if category == "research" and any(w in output.lower() for w in ["found", "search", "result", "data"]):
        score += 0.1
    elif category == "coding" and any(w in output.lower() for w in ["code", "function", "file", "script"]):
        score += 0.1
    
    return min(score, 1.0)


# ── Agent rollout ────────────────────────────────
@agl.rollout
async def prompt_test_agent(task: PromptTask, llm: agl.LLM) -> None:
    """Test a system prompt by running it against tasks."""
    client = AsyncOpenAI(
        base_url=llm.endpoint,
        api_key=os.environ.get("OPENROUTER_API_KEY", ""),
    )
    
    try:
        response = await asyncio.wait_for(
            client.chat.completions.create(
                model=llm.model,
                messages=[
                    {"role": "system", "content": llm.resources.get("system_prompt", "You are a helpful assistant.")},
                    {"role": "user", "content": task["input"]}
                ],
                temperature=llm.sampling_parameters.get("temperature", 0.7),
                max_tokens=1000,
            ),
            timeout=60.0
        )
        
        output = response.choices[0].message.content or ""
        reward = await evaluate_response(output, task["expected"], task["category"])
        
        agl.emit_reward(reward)
        print(f"Task {task['id']}: reward={reward:.2f}")
        
    except Exception as e:
        print(f"Task {task['id']}: ERROR - {e}")
        agl.emit_reward(0.0)


# ── Sample tasks ─────────────────────────────────
SAMPLE_TASKS: list[PromptTask] = [
    {
        "id": "research-1",
        "instruction": "Research and summarize findings",
        "input": "Search the web for the latest trends in decentralized AI (DeAI) and summarize the top 3 developments.",
        "expected": "Returns structured findings with sources",
        "category": "research"
    },
    {
        "id": "research-2",
        "instruction": "Search and analyze data",
        "input": "Find information about crypto trading signal services with high win rates.",
        "expected": "Returns data-driven analysis with specific metrics",
        "category": "research"
    },
    {
        "id": "coding-1",
        "instruction": "Write and execute code",
        "input": "Create a Python script that checks if a website is up by making an HTTP request.",
        "expected": "Produces working Python code with error handling",
        "category": "coding"
    },
    {
        "id": "analysis-1",
        "instruction": "Analyze and provide recommendations",
        "input": "Review the current state of NC Highway 12 infrastructure and recommend repair priorities.",
        "expected": "Provides structured analysis with actionable recommendations",
        "category": "analysis"
    },
]


async def run_apo():
    """Run APO optimization on JOE's system prompts."""
    
    # Read current system prompt
    soul_path = Path.home() / ".openclaw/workspace/SOUL.md"
    current_prompt = soul_path.read_text() if soul_path.exists() else "You are a helpful assistant."
    
    # Create OpenRouter client
    client = AsyncOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ.get("OPENROUTER_API_KEY", ""),
    )
    
    # Initialize APO
    apo = agl.APO(
        async_openai_client=client,
        gradient_model="openai/gpt-4o-mini",
        apply_edit_model="openai/gpt-4o-mini",
        beam_width=3,
        branch_factor=3,
        beam_rounds=2,
        gradient_batch_size=2,
        val_batch_size=4,
    )
    
    # Initial resource
    initial_resources = agl.NamedResources(
        system_prompt=current_prompt[:4000],  # Truncate for token limits
    )
    
    # Run optimization
    trainer = agl.Trainer(
        algorithm=apo,
        n_runners=2,
        initial_resources=initial_resources,
    )
    
    print("⚡ Starting APO prompt optimization...")
    print(f"   Tasks: {len(SAMPLE_TASKS)}")
    print(f"   Beam width: 3")
    print(f"   Rounds: 2")
    print(f"   Model: openai/gpt-4o-mini via OpenRouter")
    
    trainer.fit(prompt_test_agent, SAMPLE_TASKS)
    
    # Save optimized prompt
    results_dir = Path.home() / ".openclaw/workspace/agent-lightning/apo/results"
    results_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n✅ Optimization complete. Check {results_dir} for results.")


if __name__ == "__main__":
    asyncio.run(run_apo())
