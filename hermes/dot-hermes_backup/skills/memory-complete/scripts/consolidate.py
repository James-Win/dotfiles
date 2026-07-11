#!/usr/bin/env python3
"""Show simple project-local memory stats and duplicate-looking entries."""
import json
from collections import Counter, defaultdict
from pathlib import Path

memdir = Path('memory')
entries = []
for path in sorted(memdir.glob('*.jsonl')):
    for line in path.read_text(encoding='utf-8').splitlines():
        if line.strip():
            try:
                obj = json.loads(line)
                obj['_file'] = str(path)
                entries.append(obj)
            except json.JSONDecodeError:
                pass
print(f'entries: {len(entries)}')
print('by area:', dict(Counter(e.get('area','general') for e in entries)))
print('by priority:', dict(Counter(e.get('priority','medium') for e in entries)))

seen = defaultdict(list)
for e in entries:
    key = ' '.join(e.get('text','').lower().split())[:120]
    seen[key].append(e)

dups = {k:v for k,v in seen.items() if len(v) > 1 and k}
if dups:
    print('\npossible duplicates:')
    for k, vals in list(dups.items())[:20]:
        print(f'- {len(vals)}x {k}')
else:
    print('possible duplicates: none')
