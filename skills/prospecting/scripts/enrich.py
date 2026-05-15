#!/usr/bin/env python3
"""Enrichment runner (v0).

Reads a CSV lead list and enriches company-level metadata when possible.

Current v0 enrichment:
- If domain present: fetch website title/description via simple HTTP GET (best-effort)
- Does NOT scrape behind auth.
- Does NOT guess emails/phones.
"""

import argparse, csv, re
from pathlib import Path
from typing import Dict

import requests
from bs4 import BeautifulSoup


def norm_domain(d: str) -> str:
    d = (d or '').strip().lower()
    d = re.sub(r'^https?://', '', d)
    d = d.split('/')[0]
    return d


def fetch_meta(domain: str) -> Dict[str, str]:
    if not domain:
        return {}
    url = 'https://' + domain
    try:
        r = requests.get(url, timeout=10, headers={'User-Agent': 'openclaw-prospecting/0.1'})
        if r.status_code >= 400:
            return {}
        soup = BeautifulSoup(r.text, 'html.parser')
        title = (soup.title.string or '').strip() if soup.title else ''
        desc = ''
        tag = soup.find('meta', attrs={'name': 'description'})
        if tag and tag.get('content'):
            desc = tag.get('content').strip()
        return {'notes': (title + ' | ' + desc).strip(' |')}
    except Exception:
        return {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--in', dest='inp', required=True)
    ap.add_argument('--out', dest='out', required=True)
    args = ap.parse_args()

    inp = Path(args.inp)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    with inp.open('r', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))

    for row in rows:
        row['domain'] = norm_domain(row.get('domain',''))
        meta = fetch_meta(row.get('domain',''))
        if meta.get('notes') and not row.get('notes'):
            row['notes'] = meta['notes']

    with out.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys() if rows else [])
        if rows:
            w.writeheader()
            for r in rows:
                w.writerow(r)

    print(str(out))


if __name__ == '__main__':
    main()
