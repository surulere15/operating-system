"""
Agent Lightning Training Pipeline — Capital Recovery Agent
Train the agent to find unclaimed money more effectively.

Usage:
    python3.11 train_capital_recovery.py --mode dev      # Debug mode
    python3.11 train_capital_recovery.py --mode train     # Full training
"""

import asyncio
import json
import os
from pathlib import Path
from typing import TypedDict, Optional, List
from datetime import datetime

import agentlightning as agl
from openai import AsyncOpenAI


# ── Data structures ──────────────────────────────
class RecoveryTask(TypedDict):
    """Task for capital recovery agent."""
    id: str
    name: str
    states: list[str]
    email: str
    expected: dict  # Known results for evaluation
    difficulty: str  # easy, medium, hard


class RecoveryResult(TypedDict):
    """Result from a recovery search."""
    found: bool
    amount: float
    source: str
    confidence: float
    steps_taken: list[str]


# ── Reward function ──────────────────────────────
def compute_recovery_reward(result: dict, expected: dict) -> float:
    """Score the agent's recovery search performance."""
    score = 0.0
    
    # Did it find something? (0.3)
    if result.get("found"):
        score += 0.3
    
    # Amount accuracy (0.3)
    if expected.get("amount") and result.get("amount"):
        ratio = min(result["amount"], expected["amount"]) / max(result["amount"], expected["amount"], 1)
        score += 0.3 * ratio
    
    # Source quality (0.2)
    trusted_sources = ["missingmoney.com", "unclaimed.org", "treasury", "state"]
    if any(s in str(result.get("source", "")).lower() for s in trusted_sources):
        score += 0.2
    
    # Reasoning quality (0.2)
    steps = result.get("steps_taken", [])
    if len(steps) >= 3:
        score += 0.2
    elif len(steps) >= 1:
        score += 0.1
    
    return min(score, 1.0)


# ── Agent rollout ────────────────────────────────
@agl.rollout
async def capital_recovery_agent(task: RecoveryTask, llm: agl.LLM) -> None:
    """Capital Recovery agent rollout — searches for unclaimed money."""
    client = AsyncOpenAI(
        base_url=llm.endpoint,
        api_key=os.environ.get("OPENROUTER_API_KEY", ""),
    )
    
    system_prompt = f"""You are a Capital Recovery agent. Your job is to find unclaimed money, 
    abandoned assets, and forgotten funds for people.

    Person: {task['name']}
    States to search: {', '.join(task['states'])}
    
    Steps:
    1. Search unclaimed property databases for the person's name
    2. Check each state's treasury/unclaimed funds portal
    3. Look for abandoned bank accounts, insurance claims, tax refunds
    4. Verify findings and estimate amounts
    
    Return your findings as JSON:
    {{"found": bool, "amount": float, "source": str, "confidence": float, "steps_taken": [str]}}
    """
    
    try:
        response = await asyncio.wait_for(
            client.chat.completions.create(
                model=llm.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Search for unclaimed money for {task['name']} in {', '.join(task['states'])}."}
                ],
                temperature=llm.sampling_parameters.get("temperature", 0.5),
                max_tokens=1500,
            ),
            timeout=120.0
        )
        
        output = response.choices[0].message.content or "{}"
        
        # Parse result
        try:
            # Extract JSON from response
            import re
            json_match = re.search(r'\{[^}]+\}', output, re.DOTALL)
            result = json.loads(json_match.group()) if json_match else {"found": False, "amount": 0}
        except:
            result = {"found": False, "amount": 0, "source": "parse_error", "confidence": 0, "steps_taken": []}
        
        reward = compute_recovery_reward(result, task.get("expected", {}))
        agl.emit_reward(reward)
        
        print(f"Task {task['id']}: found={result.get('found')}, amount=${result.get('amount', 0):,.2f}, reward={reward:.2f}")
        
    except Exception as e:
        print(f"Task {task['id']}: ERROR - {e}")
        agl.emit_reward(0.0)


# ── Training dataset ─────────────────────────────
def load_training_data() -> tuple[list[RecoveryTask], list[RecoveryTask]]:
    """Load training and validation datasets."""
    
    # Sample training tasks (expand with real data)
    train_data: list[RecoveryTask] = [
        {
            "id": "recovery-001",
            "name": "John Smith",
            "states": ["Texas", "California"],
            "email": "test@example.com",
            "expected": {"found": True, "amount": 150.0, "source": "Texas Comptroller"},
            "difficulty": "easy"
        },
        {
            "id": "recovery-002",
            "name": "Maria Garcia",
            "states": ["New York", "Florida"],
            "email": "test@example.com",
            "expected": {"found": True, "amount": 2500.0, "source": "NY State Comptroller"},
            "difficulty": "medium"
        },
        {
            "id": "recovery-003",
            "name": "Robert Johnson",
            "states": ["Illinois", "Ohio", "Michigan"],
            "email": "test@example.com",
            "expected": {"found": False, "amount": 0, "source": "none"},
            "difficulty": "hard"
        },
        {
            "id": "recovery-004",
            "name": "Sarah Williams",
            "states": ["Georgia"],
            "email": "test@example.com",
            "expected": {"found": True, "amount": 75.50, "source": "Georgia DOR"},
            "difficulty": "easy"
        },
        {
            "id": "recovery-005",
            "name": "David Brown",
            "states": ["Nevada", "Arizona"],
            "email": "test@example.com",
            "expected": {"found": True, "amount": 5000.0, "source": "Nevada Treasurer"},
            "difficulty": "medium"
        },
    ]
    
    val_data: list[RecoveryTask] = [
        {
            "id": "val-001",
            "name": "Michael Davis",
            "states": ["Pennsylvania"],
            "email": "test@example.com",
            "expected": {"found": True, "amount": 300.0, "source": "PA Treasury"},
            "difficulty": "easy"
        },
        {
            "id": "val-002",
            "name": "Jennifer Miller",
            "states": ["Virginia", "Maryland"],
            "email": "test@example.com",
            "expected": {"found": False, "amount": 0, "source": "none"},
            "difficulty": "medium"
        },
    ]
    
    return train_data, val_data


async def train(mode: str = "dev"):
    """Train the Capital Recovery agent."""
    
    train_data, val_data = load_training_data()
    
    # APO config (no GPU needed)
    client = AsyncOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ.get("OPENROUTER_API_KEY", ""),
    )
    
    if mode == "dev":
        # Quick debug run
        algo = agl.APO(
            async_openai_client=client,
            gradient_model="openai/gpt-4o-mini",
            apply_edit_model="openai/gpt-4o-mini",
            beam_width=2,
            branch_factor=2,
            beam_rounds=1,
            gradient_batch_size=2,
            val_batch_size=2,
        )
        n_runners = 1
    else:
        # Full training
        algo = agl.APO(
            async_openai_client=client,
            gradient_model="openai/gpt-4o-mini",
            apply_edit_model="openai/gpt-4o-mini",
            beam_width=4,
            branch_factor=3,
            beam_rounds=3,
            gradient_batch_size=4,
            val_batch_size=4,
        )
        n_runners = 2
    
    # Initial resources
    initial_resources = agl.NamedResources(
        system_prompt="You are a Capital Recovery agent. Find unclaimed money for people.",
    )
    
    # Run training
    trainer = agl.Trainer(
        algorithm=algo,
        n_runners=n_runners,
        initial_resources=initial_resources,
    )
    
    print(f"⚡ Training Capital Recovery Agent ({mode} mode)")
    print(f"   Train tasks: {len(train_data)}")
    print(f"   Val tasks: {len(val_data)}")
    print(f"   Model: openai/gpt-4o-mini via OpenRouter")
    print()
    
    trainer.fit(capital_recovery_agent, train_data, val_dataset=val_data)
    
    # Save results
    results_dir = Path.home() / ".openclaw/workspace/agent-lightning/training/results"
    results_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = results_dir / f"capital_recovery_{mode}_{timestamp}.json"
    
    print(f"\n✅ Training complete. Results saved to {results_file}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["dev", "train"], default="dev")
    args = parser.parse_args()
    
    asyncio.run(train(args.mode))
