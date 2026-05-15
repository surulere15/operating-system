#!/usr/bin/env python3
"""Prospecting job runner (v0).

Goal: create a *repeatable* prospecting artifact even when provider APIs are not configured.

Strategy:
- Always produce a job file + empty-but-valid lead list schema.
- If CLEARBIT_API_KEY is available, allow basic company enrichment.

NOTE: This v0 does NOT claim verified emails/phones.
"""

import argparse, csv, json, os, re
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

LEADS_DIR = Path('/Users/sam/.openclaw/workspace/leads')

@dataclass
class Lead:
    company: str = ""
    domain: str = ""
    country: str = ""
    tags: str = ""
    source: str = ""
    notes: str = ""
    # person fields (optional)
    name: str = ""
    title: str = ""
    linkedin: str = ""
    email: str = ""
    phone: str = ""
    confidence: str = ""


def slugify(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "job"


def write_csv(path: Path, leads: List[Lead]):
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(asdict(Lead()).keys())
    with path.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for l in leads:
            w.writerow(asdict(l))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--name', default='', help='job name (folder)')
    ap.add_argument('--prompt', required=True)
    ap.add_argument('--limit', type=int, default=50)
    args = ap.parse_args()

    name = slugify(args.name or args.prompt)
    out_dir = LEADS_DIR / name
    out_dir.mkdir(parents=True, exist_ok=True)

    job = {
        'name': name,
        'prompt': args.prompt,
        'limit': args.limit,
        'created_at': datetime.utcnow().isoformat() + 'Z',
        'adapters': {
            'clearbit': bool(os.getenv('CLEARBIT_API_KEY')),
            'pdl': bool(os.getenv('PDL_API_KEY')),
            'apollo': bool(os.getenv('APOLLO_API_KEY')),
        },
        'status': 'CREATED',
        'notes': 'v0 scaffold. Add a provider adapter for verified contacts.'
    }

    # v0: produce empty list but correct schema
    leads: List[Lead] = []

    (out_dir / 'job.json').write_text(json.dumps(job, indent=2), encoding='utf-8')
    (out_dir / 'leads.json').write_text(json.dumps([asdict(l) for l in leads], indent=2), encoding='utf-8')
    write_csv(out_dir / 'leads.csv', leads)

    print(str(out_dir))


if __name__ == '__main__':
    main()
