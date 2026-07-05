#!/usr/bin/env python3
"""Simple keyword recall over ./memory/*.jsonl."""
import argparse, json, re
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('query', nargs='+')
p.add_argument('--dir', default='memory')
p.add_argument('--limit', type=int, default=10)
args = p.parse_args()
terms = [q.lower() for q in args.query]
rows = []
for path in sorted(Path(args.dir).glob('*.jsonl'), reverse=True):
    try:
        lines = path.read_text(encoding='utf-8').splitlines()
    except FileNotFoundError:
        continue
    for line in lines:
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        hay = json.dumps(obj, ensure_ascii=False).lower()
        score = sum(hay.count(t) for t in terms)
        if score:
            rows.append((score, obj.get('timestamp',''), path.name, obj))
rows.sort(key=lambda x: (x[0], x[1]), reverse=True)
for score, ts, fname, obj in rows[:args.limit]:
    print(f'[{score}] {ts} {fname} {obj.get("area","general")}/{obj.get("priority","medium")}')
    print(obj.get('text',''))
    if obj.get('tags'):
        print('tags:', ', '.join(obj['tags']))
    print('---')
if not rows:
    print('no matches')
