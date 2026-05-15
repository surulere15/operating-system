#!/usr/bin/env python3
"""Raw digging prospecting (no paid providers).

Goal: produce a *useful* lead list from public web signals.

What it can do:
- Uses Brave web_search via OpenClaw is not accessible from inside Python.
- Instead, this script takes a list of seed URLs (search results) and extracts:
  - company name
  - domain
  - contact emails found on site (best-effort)
  - UK hints (TLD .uk, address, footer)
  - n8n usage hints (mentions 'n8n', 'n8n.io', 'workflow automation', etc.)

How to use (recommended):
1) Use the assistant to gather seed URLs via web_search/browser.
2) Pass them into this script via --seeds-file.

Outputs CSV/JSON under workspace/leads/<job>/.

No fabrication, no behind-login scraping.
"""

import argparse, csv, json, re
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Dict

import requests
from bs4 import BeautifulSoup

LEADS_DIR = Path('/Users/sam/.openclaw/workspace/leads')

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")

@dataclass
class Lead:
    company: str = ''
    domain: str = ''
    country: str = ''
    tags: str = ''
    source: str = ''
    notes: str = ''
    name: str = ''
    title: str = ''
    linkedin: str = ''
    email: str = ''
    phone: str = ''
    confidence: str = ''


def slugify(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = re.sub(r"_+", "_", s).strip('_')
    return s or 'job'


def norm_domain(url: str) -> str:
    url = (url or '').strip()
    url = re.sub(r'^https?://', '', url)
    url = url.split('/')[0]
    return url.lower()


def fetch(url: str) -> str:
    try:
        r = requests.get(url, timeout=15, headers={'User-Agent': 'openclaw-prospecting/raw/0.1'})
        if r.status_code >= 400:
            return ''
        return r.text
    except Exception:
        return ''


def extract_emails(text: str) -> List[str]:
    if not text:
        return []
    emails = set(m.group(0) for m in EMAIL_RE.finditer(text))
    # filter common junk
    bad = {'example.com', 'email.com'}
    out=[]
    for e in emails:
        dom = e.split('@')[-1]
        if dom in bad:
            continue
        out.append(e)
    return sorted(out)[:5]


def parse_company(html: str) -> Dict[str, str]:
    if not html:
        return {}
    soup = BeautifulSoup(html, 'html.parser')
    title = (soup.title.string or '').strip() if soup.title else ''
    desc = ''
    tag = soup.find('meta', attrs={'name':'description'})
    if tag and tag.get('content'):
        desc = tag.get('content').strip()
    text = soup.get_text(' ', strip=True)
    return {'title': title, 'desc': desc, 'text': text[:20000]}


def uk_hint(text: str, domain: str) -> bool:
    t = (text or '').lower()
    if domain.endswith('.uk'):
        return True
    if 'united kingdom' in t or 'london' in t or 'manchester' in t or 'edinburgh' in t:
        return True
    if re.search(r"\bUK\b", text or ''):
        return True
    return False


def n8n_hint(text: str) -> bool:
    t = (text or '').lower()
    return ('n8n' in t) or ('n8n.io' in t)


def write_csv(path: Path, leads: List[Lead]):
    fields = list(asdict(Lead()).keys())
    with path.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for l in leads:
            w.writerow(asdict(l))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--name', default='')
    ap.add_argument('--prompt', required=True)
    ap.add_argument('--seeds-file', required=True, help='Text file: one URL per line')
    ap.add_argument('--limit', type=int, default=50)
    args = ap.parse_args()

    name = slugify(args.name or args.prompt)
    out_dir = LEADS_DIR / name
    out_dir.mkdir(parents=True, exist_ok=True)

    seeds = [l.strip() for l in Path(args.seeds_file).read_text(encoding='utf-8').splitlines() if l.strip()]
    leads: List[Lead] = []

    for u in seeds:
        if len(leads) >= args.limit:
            break
        dom = norm_domain(u)
        if not dom:
            continue
        html = fetch(u if u.startswith('http') else 'https://' + u)
        meta = parse_company(html)
        text = meta.get('text','')
        emails = extract_emails(html + '\n' + text)

        tags=[]
        if n8n_hint(text): tags.append('n8n_hint')
        if uk_hint(text, dom): tags.append('uk_hint')

        leads.append(Lead(
            company=meta.get('title','')[:120],
            domain=dom,
            country='UK' if uk_hint(text, dom) else '',
            tags=','.join(tags),
            source=u,
            notes=(' | '.join([meta.get('title',''), meta.get('desc','')])[:400]).strip(' |'),
            email=emails[0] if emails else '',
            confidence='low' if emails else 'n/a'
        ))

    job = {
        'name': name,
        'prompt': args.prompt,
        'limit': args.limit,
        'created_at': datetime.utcnow().isoformat() + 'Z',
        'seeds_count': len(seeds),
        'status': 'DONE',
        'notes': 'raw digging from public web. emails/phones not verified.'
    }

    (out_dir / 'job.json').write_text(json.dumps(job, indent=2), encoding='utf-8')
    (out_dir / 'leads.json').write_text(json.dumps([asdict(l) for l in leads], indent=2), encoding='utf-8')
    write_csv(out_dir / 'leads.csv', leads)

    print(str(out_dir))


if __name__ == '__main__':
    main()
