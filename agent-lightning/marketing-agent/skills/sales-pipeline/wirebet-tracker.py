#!/usr/bin/env python3
"""
Wirebet Deal Tracker — Track and score outreach leads for wirebet.com.

Adapted from ai-marketing-skills/sales-pipeline/deal_resurrector.py.

Tracks:
- DM/email outreach attempts
- Response status
- Follow-up scheduling
- Deal scoring (time decay + interest signals)

Usage:
    # Add a lead
    python3 wirebet-tracker.py add --name "Shayne Coplan" --company "Polymarket" \
      --channel twitter --status "sent"

    # Update lead status
    python3 wirebet-tracker.py update --lead LEAD-001 --status "replied" \
      --notes "Interested, asked for price"

    # Score all leads
    python3 wirebet-tracker.py score

    # Show pipeline
    python3 wirebet-tracker.py pipeline

    # Follow-ups due
    python3 wirebet-tracker.py followups
"""

import argparse
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

BASE_DIR = Path(os.path.expanduser("~/.openclaw/workspace/agent-lightning/marketing-agent/data"))
BASE_DIR.mkdir(parents=True, exist_ok=True)

LEADS_FILE = BASE_DIR / "leads.json"

STATUS_WEIGHTS = {
    "sent": 0.3,
    "opened": 0.5,
    "replied": 0.8,
    "interested": 0.9,
    "negotiating": 0.95,
    "closed_won": 1.0,
    "closed_lost": 0.0,
    "no_response": 0.1,
}

CHANNEL_WEIGHTS = {
    "twitter_dm": 0.7,
    "email": 0.8,
    "linkedin": 0.6,
    "website_form": 0.9,
}


def load_leads():
    if LEADS_FILE.exists():
        return json.loads(LEADS_FILE.read_text())
    return {"leads": [], "next_id": 1}


def save_leads(data):
    LEADS_FILE.write_text(json.dumps(data, indent=2))


def add_lead(args):
    data = load_leads()
    
    lead = {
        "id": f"LEAD-{data['next_id']:03d}",
        "name": args.name,
        "company": args.company,
        "role": args.role or "Unknown",
        "channel": args.channel,
        "status": args.status or "sent",
        "notes": args.notes or "",
        "created": datetime.now(timezone.utc).isoformat(),
        "updated": datetime.now(timezone.utc).isoformat(),
        "follow_up_due": (datetime.now(timezone.utc) + timedelta(days=3)).isoformat(),
        "interactions": [
            {
                "type": "outreach",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "channel": args.channel,
                "notes": "Initial outreach sent",
            }
        ],
    }
    
    data["leads"].append(lead)
    data["next_id"] += 1
    save_leads(data)
    
    print(f"✅ Added {lead['id']}: {args.name} ({args.company})")
    print(f"   Channel: {args.channel} | Status: {lead['status']}")
    print(f"   Follow-up due: {lead['follow_up_due'][:10]}")


def update_lead(args):
    data = load_leads()
    
    lead = next((l for l in data["leads"] if l["id"] == args.lead), None)
    if not lead:
        print(f"❌ Lead {args.lead} not found")
        return
    
    old_status = lead["status"]
    lead["status"] = args.status
    lead["updated"] = datetime.now(timezone.utc).isoformat()
    
    if args.notes:
        lead["notes"] = args.notes
    
    # Add interaction
    lead["interactions"].append({
        "type": "status_change",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "from": old_status,
        "to": args.status,
        "notes": args.notes or "",
    })
    
    # Update follow-up
    if args.status in ["replied", "interested", "negotiating"]:
        lead["follow_up_due"] = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    elif args.status == "sent":
        lead["follow_up_due"] = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()
    
    save_leads(data)
    print(f"✅ Updated {args.lead}: {old_status} → {args.status}")


def score_leads(args):
    data = load_leads()
    
    print(f"\n📊 LEAD SCORING ({len(data['leads'])} leads)\n")
    
    scored = []
    for lead in data["leads"]:
        # Base score from status
        status_score = STATUS_WEIGHTS.get(lead["status"], 0.1)
        
        # Channel weight
        channel_score = CHANNEL_WEIGHTS.get(lead["channel"], 0.5)
        
        # Time decay (older leads score lower unless active)
        created = datetime.fromisoformat(lead["created"])
        age_days = (datetime.now(timezone.utc) - created).days
        time_decay = max(0.3, 1.0 - (age_days * 0.05))
        
        # Interaction bonus
        interaction_bonus = min(0.2, len(lead.get("interactions", [])) * 0.05)
        
        # Final score
        score = (status_score * 0.5) + (channel_score * 0.2) + (time_decay * 0.2) + (interaction_bonus * 0.1)
        score = round(score * 100, 1)
        
        scored.append({**lead, "score": score})
    
    scored.sort(key=lambda x: x["score"], reverse=True)
    
    for lead in scored:
        emoji = "🟢" if lead["score"] >= 70 else "🟡" if lead["score"] >= 40 else "🔴"
        print(f"  {emoji} {lead['id']}: {lead['name']} ({lead['company']}) — Score: {lead['score']}")
        print(f"     Status: {lead['status']} | Channel: {lead['channel']}")
        print()


def show_pipeline(args):
    data = load_leads()
    
    stages = {}
    for lead in data["leads"]:
        stage = lead["status"]
        stages.setdefault(stage, []).append(lead)
    
    print(f"\n📋 WIREFET PIPELINE ({len(data['leads'])} leads)\n")
    for stage in ["sent", "opened", "replied", "interested", "negotiating", "closed_won", "closed_lost"]:
        leads = stages.get(stage, [])
        print(f"  {stage.upper()}: {len(leads)}")
        for lead in leads:
            print(f"    • {lead['name']} ({lead['company']}) — {lead['channel']}")
    print()


def show_followups(args):
    data = load_leads()
    now = datetime.now(timezone.utc)
    
    due = []
    for lead in data["leads"]:
        if lead["status"] in ["closed_won", "closed_lost"]:
            continue
        follow_up = datetime.fromisoformat(lead["follow_up_due"])
        if follow_up <= now:
            due.append(lead)
    
    if not due:
        print("✅ No follow-ups due right now")
        return
    
    print(f"\n⏰ FOLLOW-UPS DUE ({len(due)})\n")
    for lead in due:
        print(f"  → {lead['name']} ({lead['company']})")
        print(f"    Status: {lead['status']} | Last contact: {lead['updated'][:10]}")
        print(f"    Notes: {lead['notes'] or 'No notes'}")
        print()


def main():
    parser = argparse.ArgumentParser(description="Wirebet Deal Tracker")
    sub = parser.add_subparsers(dest="command")
    
    p = sub.add_parser("add")
    p.add_argument("--name", required=True)
    p.add_argument("--company", required=True)
    p.add_argument("--role")
    p.add_argument("--channel", required=True)
    p.add_argument("--status")
    p.add_argument("--notes")
    
    p = sub.add_parser("update")
    p.add_argument("--lead", required=True)
    p.add_argument("--status", required=True)
    p.add_argument("--notes")
    
    sub.add_parser("score")
    sub.add_parser("pipeline")
    sub.add_parser("followups")
    
    args = parser.parse_args()
    
    commands = {
        "add": add_lead,
        "update": update_lead,
        "score": score_leads,
        "pipeline": show_pipeline,
        "followups": show_followups,
    }
    
    if args.command in commands:
        commands[args.command](args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
