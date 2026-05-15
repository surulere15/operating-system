#!/usr/bin/env python3
"""
Wirebet Experiment Engine — Test marketing variants with real statistics.

Uses bootstrap confidence intervals and Mann-Whitney U tests from
ai-marketing-skills/experiment-engine.py, adapted for domain sale marketing.

Usage:
    # Create a Twitter experiment
    python3 wirebet-experiments.py create --channel twitter \
      --hypothesis "Thread posts get 2x impressions vs single posts" \
      --variable format --variants '["thread", "single"]' --metric impressions

    # Log results
    python3 wirebet-experiments.py log --experiment EXP-001 --variant thread \
      --metrics '{"impressions": 4500, "clicks": 120, "replies": 8}'

    # Score experiment
    python3 wirebet-experiments.py score --experiment EXP-001

    # View playbook (winners)
    python3 wirebet-experiments.py playbook

    # Suggest next experiment
    python3 wirebet-experiments.py suggest
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy import stats

BASE_DIR = Path(os.path.expanduser("~/.openclaw/workspace/agent-lightning/marketing-agent/data/experiments"))
BASE_DIR.mkdir(parents=True, exist_ok=True)

EXPERIMENTS_FILE = BASE_DIR / "experiments.json"
PLAYBOOK_FILE = BASE_DIR / "playbook.json"

BOOTSTRAP_ITERATIONS = 1000
P_WINNER = 0.05
P_TREND = 0.10
LIFT_WIN = 15.0


def load_experiments():
    if EXPERIMENTS_FILE.exists():
        return json.loads(EXPERIMENTS_FILE.read_text())
    return {"experiments": [], "next_id": 1}


def save_experiments(data):
    EXPERIMENTS_FILE.write_text(json.dumps(data, indent=2))


def load_playbook():
    if PLAYBOOK_FILE.exists():
        return json.loads(PLAYBOOK_FILE.read_text())
    return {"winners": [], "updated": None}


def save_playbook(data):
    data["updated"] = datetime.now(timezone.utc).isoformat()
    PLAYBOOK_FILE.write_text(json.dumps(data, indent=2))


def bootstrap_lift_ci(a_vals, b_vals, n_iter=BOOTSTRAP_ITERATIONS, ci=95):
    if len(a_vals) == 0 or len(b_vals) == 0:
        return None, None
    mean_a = np.mean(a_vals)
    if mean_a == 0:
        return None, None
    lifts = []
    for _ in range(n_iter):
        a_sample = np.random.choice(a_vals, size=len(a_vals), replace=True)
        b_sample = np.random.choice(b_vals, size=len(b_vals), replace=True)
        lift = (np.mean(b_sample) - np.mean(a_sample)) / np.mean(a_sample) * 100
        lifts.append(lift)
    lower = np.percentile(lifts, (100 - ci) / 2)
    upper = np.percentile(lifts, 100 - (100 - ci) / 2)
    return lower, upper


def create_experiment(args):
    data = load_experiments()
    variants = json.loads(args.variants)
    
    exp = {
        "id": f"EXP-{data['next_id']:03d}",
        "channel": args.channel,
        "hypothesis": args.hypothesis,
        "variable": args.variable,
        "variants": variants,
        "metric": args.metric,
        "status": "active",
        "created": datetime.now(timezone.utc).isoformat(),
        "data_points": {v: [] for v in variants},
        "result": None,
    }
    
    data["experiments"].append(exp)
    data["next_id"] += 1
    save_experiments(data)
    
    print(f"✅ Created {exp['id']}: {args.hypothesis}")
    print(f"   Channel: {args.channel}")
    print(f"   Variants: {', '.join(variants)}")
    print(f"   Metric: {args.metric}")


def log_data(args):
    data = load_experiments()
    metrics = json.loads(args.metrics)
    
    exp = next((e for e in data["experiments"] if e["id"] == args.experiment), None)
    if not exp:
        print(f"❌ Experiment {args.experiment} not found")
        return
    
    if args.variant not in exp["data_points"]:
        print(f"❌ Variant '{args.variant}' not in experiment")
        return
    
    exp["data_points"][args.variant].append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "metrics": metrics,
    })
    
    save_experiments(data)
    print(f"✅ Logged data point for {args.experiment} / {args.variant}")
    print(f"   {args.variant}: {exp['metric']} = {metrics.get(exp['metric'], 'N/A')}")


def score_experiment(args):
    data = load_experiments()
    exp = next((e for e in data["experiments"] if e["id"] == args.experiment), None)
    
    if not exp:
        print(f"❌ Experiment {args.experiment} not found")
        return
    
    metric = exp["metric"]
    variants = exp["variants"]
    
    if len(variants) != 2:
        print("⚠️  Scoring only supports 2 variants (A/B)")
        return
    
    a_data = [dp["metrics"].get(metric, 0) for dp in exp["data_points"].get(variants[0], [])]
    b_data = [dp["metrics"].get(metric, 0) for dp in exp["data_points"].get(variants[1], [])]
    
    print(f"\n📊 {exp['id']}: {exp['hypothesis']}")
    print(f"   Variant A ({variants[0]}): n={len(a_data)}, mean={np.mean(a_data):.1f}")
    print(f"   Variant B ({variants[1]}): n={len(b_data)}, mean={np.mean(b_data):.1f}")
    
    if len(a_data) < 5 or len(b_data) < 5:
        print(f"   ⚠️  Need more data (min 5 per variant)")
        return
    
    # Mann-Whitney U test
    u_stat, p_value = stats.mannwhitneyu(a_data, b_data, alternative='two-sided')
    
    # Bootstrap CI for lift
    ci_lower, ci_upper = bootstrap_lift_ci(a_data, b_data)
    lift = (np.mean(b_data) - np.mean(a_data)) / np.mean(a_data) * 100 if np.mean(a_data) > 0 else 0
    
    print(f"   Lift: {lift:+.1f}%")
    print(f"   95% CI: [{ci_lower:+.1f}%, {ci_upper:+.1f}%]")
    print(f"   p-value: {p_value:.4f}")
    
    if p_value < P_WINNER and lift > LIFT_WIN:
        winner = variants[1] if np.mean(b_data) > np.mean(a_data) else variants[0]
        print(f"\n   🏆 WINNER: {winner} (p={p_value:.4f}, lift={lift:+.1f}%)")
        
        exp["status"] = "completed"
        exp["result"] = {"winner": winner, "p_value": p_value, "lift": lift}
        save_experiments(data)
        
        # Add to playbook
        playbook = load_playbook()
        playbook["winners"].append({
            "experiment": exp["id"],
            "channel": exp["channel"],
            "variable": exp["variable"],
            "winner": winner,
            "lift": lift,
            "p_value": p_value,
            "promoted": datetime.now(timezone.utc).isoformat(),
        })
        save_playbook(playbook)
        print(f"   📖 Added to playbook")
    elif p_value < P_TREND:
        print(f"   📈 TRENDING: {variants[1] if np.mean(b_data) > np.mean(a_data) else variants[0]}")
    else:
        print(f"   ⏳ No significant difference yet")


def show_playbook(args):
    playbook = load_playbook()
    
    if not playbook["winners"]:
        print("📖 Playbook is empty. Run experiments to populate it.")
        return
    
    print(f"\n📖 PLAYBOOK ({len(playbook['winners'])} winners)\n")
    for w in playbook["winners"]:
        print(f"  {w['experiment']}: {w['variable']} → {w['winner']} ({w['lift']:+.1f}% lift, p={w['p_value']:.4f})")


def suggest_experiment(args):
    playbook = load_playbook()
    winners = {w["variable"] for w in playbook.get("winners", [])}
    
    suggestions = []
    
    # Twitter content experiments
    if "format" not in winners:
        suggestions.append({
            "channel": "twitter",
            "hypothesis": "Thread posts get 2x impressions vs single posts",
            "variable": "format",
            "variants": ["thread", "single"],
            "metric": "impressions",
        })
    
    if "timing" not in winners:
        suggestions.append({
            "channel": "twitter",
            "hypothesis": "Morning posts (9-11am) get 1.5x engagement vs evening",
            "variable": "timing",
            "variants": ["morning", "evening"],
            "metric": "engagement",
        })
    
    if "hook_type" not in winners:
        suggestions.append({
            "channel": "twitter",
            "hypothesis": "Stat-based hooks outperform question hooks",
            "variable": "hook_type",
            "variants": ["stat", "question"],
            "metric": "clicks",
        })
    
    if "cta_type" not in winners:
        suggestions.append({
            "channel": "outreach",
            "hypothesis": "DM with link outperforms DM without link",
            "variable": "cta_type",
            "variants": ["with_link", "without_link"],
            "metric": "replies",
        })
    
    print(f"\n💡 SUGGESTED EXPERIMENTS ({len(suggestions)} available)\n")
    for i, s in enumerate(suggestions, 1):
        print(f"  {i}. {s['hypothesis']}")
        print(f"     Channel: {s['channel']} | Variable: {s['variable']}")
        print(f"     Variants: {', '.join(s['variants'])} | Metric: {s['metric']}")
        print()


def list_experiments(args):
    data = load_experiments()
    active = [e for e in data["experiments"] if e["status"] == "active"]
    
    if not active:
        print("No active experiments. Create one with 'create' command.")
        return
    
    print(f"\n📋 ACTIVE EXPERIMENTS ({len(active)})\n")
    for e in active:
        total_points = sum(len(v) for v in e["data_points"].values())
        print(f"  {e['id']}: {e['hypothesis']}")
        print(f"     Channel: {e['channel']} | Variants: {', '.join(e['variants'])}")
        print(f"     Data points: {total_points} | Created: {e['created'][:10]}")


def main():
    parser = argparse.ArgumentParser(description="Wirebet Experiment Engine")
    sub = parser.add_subparsers(dest="command")
    
    # Create
    p = sub.add_parser("create")
    p.add_argument("--channel", required=True)
    p.add_argument("--hypothesis", required=True)
    p.add_argument("--variable", required=True)
    p.add_argument("--variants", required=True)
    p.add_argument("--metric", required=True)
    
    # Log
    p = sub.add_parser("log")
    p.add_argument("--experiment", required=True)
    p.add_argument("--variant", required=True)
    p.add_argument("--metrics", required=True)
    
    # Score
    p = sub.add_parser("score")
    p.add_argument("--experiment", required=True)
    
    # Playbook
    sub.add_parser("playbook")
    
    # Suggest
    sub.add_parser("suggest")
    
    # List
    sub.add_parser("list")
    
    args = parser.parse_args()
    
    commands = {
        "create": create_experiment,
        "log": log_data,
        "score": score_experiment,
        "playbook": show_playbook,
        "suggest": suggest_experiment,
        "list": list_experiments,
    }
    
    if args.command in commands:
        commands[args.command](args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
