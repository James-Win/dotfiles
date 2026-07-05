#!/usr/bin/env python3
"""Append a project-local memory fact to ./memory/YYYY-MM-DD.jsonl."""
import argparse, json, os
from datetime import datetime, timezone
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('--text', required=True, help='Fact or note to capture')
p.add_argument('--area', default='general')
p.add_argument('--priority', default='medium', choices=['low','medium','high','critical'])
p.add_argument('--source', default='manual')
p.add_argument('--tags', default='', help='Comma-separated tags')
p.add_argument('--dir', default='memory', help='Memory directory, default ./memory')
args = p.parse_args()

now = datetime.now(timezone.utc)
outdir = Path(args.dir)
outdir.mkdir(parents=True, exist_ok=True)
entry = {
    'timestamp': now.isoformat(),
    'area': args.area,
    'priority': args.priority,
    'source': args.source,
    'tags': [t.strip() for t in args.tags.split(',') if t.strip()],
    'text': args.text,
}
path = outdir / f'{now.date().isoformat()}.jsonl'
with path.open('a', encoding='utf-8') as f:
    f.write(json.dumps(entry, ensure_ascii=False) + '\n')
print(f'captured: {path}')
