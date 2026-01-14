#!/usr/bin/env python3
"""Summarize differences between house systems from sweep results."""
import json
from pathlib import Path
from collections import defaultdict

IN_PATH = Path('artifacts/house_system_sweep_results.json')
OUT_PATH = Path('artifacts/house_system_sweep_diff_summary.txt')

data = json.loads(IN_PATH.read_text(encoding='utf8'))
results = data.get('results', {})
systems = data.get('systems', [])

# Map pair -> count of datetimes/locations where differences exist and total difference count
def _pair_default():
    return {'cases': 0, 'diff_count': 0, 'examples': []}

pair_stats = defaultdict(_pair_default)

for dt, locs in results.items():
    for loc_key, sysmap in locs.items():
        keys = sorted(sysmap.keys(), key=lambda x: str(x))
        for i in range(len(keys)):
            for j in range(i+1, len(keys)):
                a = keys[i]; b = keys[j]
                aobj = sysmap.get(a, {})
                bobj = sysmap.get(b, {})
                if 'planets' not in aobj or 'planets' not in bobj:
                    continue
                diffs = []
                allp = set(aobj['planets'].keys()) | set(bobj['planets'].keys())
                for pn in sorted(allp):
                    v1 = aobj['planets'].get(pn)
                    v2 = bobj['planets'].get(pn)
                    if v1 != v2:
                        diffs.append(f"{pn}: {v1} vs {v2}")
                if diffs:
                    key = f"{a} <> {b}"
                    pair_stats[key]['cases'] += 1
                    pair_stats[key]['diff_count'] += len(diffs)
                    if len(pair_stats[key]['examples']) < 5:
                        pair_stats[key]['examples'].append({'dt': dt, 'loc': loc_key, 'diffs': diffs[:10]})

# Write summary
with OUT_PATH.open('w', encoding='utf8') as f:
    f.write('House system sweep diff summary\n')
    f.write('Generated from artifacts/house_system_sweep_results.json\n\n')
    if not pair_stats:
        f.write('No differences found across any checked pairs.\n')
    else:
        # sort pairs by cases desc
        items = sorted(pair_stats.items(), key=lambda kv: (-kv[1]['cases'], -kv[1]['diff_count'], kv[0]))
        for pair, stats in items:
            f.write(f"Pair: {pair}\n")
            f.write(f"  Cases with differences: {stats['cases']}\n")
            f.write(f"  Total planet diffs (sum): {stats['diff_count']}\n")
            f.write(f"  Example differences (up to 5):\n")
            for ex in stats['examples']:
                f.write(f"    - {ex['dt']} @ {ex['loc']}\n")
                for d in ex['diffs']:
                    f.write(f"       {d}\n")
            f.write('\n')

print('WROTE', OUT_PATH)
