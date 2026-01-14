#!/usr/bin/env python3
"""Expanded house system sweep.
Runs horoscopes across a larger set of datetimes and locations, writes JSON results and a CSV summary of pairwise diffs.
"""
import requests
import json
import itertools
import csv
from pathlib import Path
from datetime import datetime

BASE = "http://localhost:8080"
OUT_DIR = Path("./artifacts")
OUT_DIR.mkdir(exist_ok=True)

def fetch_house_systems():
    r = requests.get(f"{BASE}/api/house_systems", timeout=10)
    r.raise_for_status()
    data = r.json()
    return [str(item['key']) for item in data.get('items', [])]

def create_horo(dt_iso, loc, houseSystem):
    body = {
        'birthDateTime': dt_iso,
        'location': loc,
        'ayanamsaMode': 'TRUE_CITRA',
        'houseSystem': str(houseSystem)
    }
    r = requests.post(f"{BASE}/api/horoscope", json=body, timeout=30)
    r.raise_for_status()
    return r.json()

def run():
    systems = fetch_house_systems()
    # limit to 12 systems to keep runtime reasonable
    if len(systems) > 12:
        systems = systems[:12]

    # expanded datetimes (20 samples across years)
    datetimes = [
        "1970-01-01T00:00:00",
        "1980-06-15T12:30:00",
        "1990-03-21T03:15:00",
        "1992-11-03T09:15:00",
        "1995-08-12T18:45:00",
        "2000-01-01T06:30:00",
        "2004-04-04T04:04:00",
        "2008-09-09T09:09:00",
        "2010-07-01T12:00:00",
        "2012-12-12T12:12:00",
        "2016-02-29T23:59:00",
        "2018-05-05T05:05:00",
        "2020-12-21T00:00:00",
        "2021-03-20T10:00:00",
        "2022-11-11T11:11:00",
        "2023-06-01T14:30:00",
        "2024-02-29T08:00:00",
        "2024-12-31T23:59:00",
        "2025-01-01T00:01:00",
        datetime.utcnow().replace(microsecond=0).isoformat(),
    ]

    locations = [
        { 'place': 'Chennai,IN', 'tzOffset': 5.5, 'latitude': 13.0827, 'longitude': 80.2707 },
        { 'place': 'Bengaluru,IN', 'tzOffset': 5.5, 'latitude': 12.9716, 'longitude': 77.5946 },
        { 'place': 'London,GB', 'tzOffset': 0.0, 'latitude': 51.5074, 'longitude': -0.1278 },
        { 'place': 'New York,US', 'tzOffset': -5.0, 'latitude': 40.7128, 'longitude': -74.0060 },
        { 'place': 'Sydney,AU', 'tzOffset': 10.0, 'latitude': -33.8688, 'longitude': 151.2093 },
        { 'place': 'Reykjavik,IS', 'tzOffset': 0.0, 'latitude': 64.1466, 'longitude': -21.9426 },
    ]

    results = {}
    total = len(datetimes) * len(locations) * len(systems)
    done = 0
    for dt in datetimes:
        results.setdefault(dt, {})
        for loc in locations:
            loc_key = loc['place'].split(',')[0]
            results[dt].setdefault(loc_key, {})
            for hs in systems:
                done += 1
                print(f"[{done}/{total}] {dt} {loc_key} {hs}")
                try:
                    resp = create_horo(dt, loc, hs)
                except Exception as e:
                    print('  ERROR:', e)
                    results[dt][loc_key][str(hs)] = {'error': str(e)}
                    continue
                planets = {}
                for p in resp.get('rasiChart', {}).get('planets', []):
                    planets[p['name']] = p.get('houseAbs')
                results[dt][loc_key][str(hs)] = {'meta': resp.get('meta', {}), 'planets': planets}

    # write full JSON
    out_json = OUT_DIR / 'house_system_sweep_expand_results.json'
    with out_json.open('w', encoding='utf8') as f:
        json.dump({'generatedAt': datetime.utcnow().isoformat(), 'systems': systems, 'results': results}, f, indent=2)

    # produce CSV summary of pairwise diffs per dt/loc
    out_csv = OUT_DIR / 'house_system_sweep_expand_diffs.csv'
    with out_csv.open('w', newline='', encoding='utf8') as csvf:
        writer = csv.DictWriter(csvf, fieldnames=['datetime','location','pair','diff_count','diffs_sample'])
        writer.writeheader()
        for dt, locs in results.items():
            for loc_key, sysmap in locs.items():
                keys = sorted(sysmap.keys(), key=lambda x: str(x))
                for a,b in itertools.combinations(keys, 2):
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
                            diffs.append(f"{pn}:{v1}->{v2}")
                    if diffs:
                        writer.writerow({'datetime': dt, 'location': loc_key, 'pair': f"{a}<>{b}", 'diff_count': len(diffs), 'diffs_sample': ';'.join(diffs[:8])})

    print('WROTE', out_json)
    print('WROTE', out_csv)

if __name__ == '__main__':
    run()
