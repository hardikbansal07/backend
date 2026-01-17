#!/usr/bin/env python3
"""House system sweep: compare planet.houseAbs across house systems for several datetimes/locations.
Writes results to artifacts/house_system_sweep_results.json and a text report.
"""
import requests
import json
import itertools
from pathlib import Path
from datetime import datetime

BASE = "http://localhost:8080"
OUT_DIR = Path("./artifacts")
OUT_DIR.mkdir(exist_ok=True)

def fetch_house_systems():
    r = requests.get(f"{BASE}/api/house_systems", timeout=10)
    r.raise_for_status()
    data = r.json()
    # return list of keys (use key field as-is)
    return [item['key'] for item in data.get('items', [])]

def create_horo(dt_iso, loc, houseSystem):
    body = {
        'birthDateTime': dt_iso,
        'location': loc,
        'ayanamsaMode': 'TRUE_CITRA',
        'houseSystem': houseSystem
    }
    r = requests.post(f"{BASE}/api/horoscope", json=body, timeout=20)
    r.raise_for_status()
    return r.json()

def run():
    systems = fetch_house_systems()
    # pick a subset if there are many (limit to 12)
    if len(systems) > 12:
        systems = systems[:12]

    datetimes = [
        "1992-11-03T09:15:00",
        "2000-01-01T06:30:00",
        "1988-06-15T23:45:00",
        "2010-07-01T12:00:00",
        "2020-12-21T00:00:00",
    ]

    locations = [
        { 'place': 'Chennai,IN', 'tzOffset': 5.5, 'latitude': 13.0827, 'longitude': 80.2707 },
        { 'place': 'London,GB', 'tzOffset': 0.0, 'latitude': 51.5074, 'longitude': -0.1278 },
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
                # coerce house-system key to string before posting (server treats numeric keys inconsistently)
                hs_str = str(hs)
                print(f"[{done}/{total}] {dt} {loc_key} {hs_str}")
                try:
                    resp = create_horo(dt, loc, hs_str)
                except Exception as e:
                    print("  ERROR:", e)
                    results[dt][loc_key][str(hs)] = {'error': str(e)}
                    continue
                # extract planet houseAbs mapping
                planets = {}
                try:
                    for p in resp.get('rasiChart', {}).get('planets', []):
                        planets[p['name']] = p.get('houseAbs')
                except Exception:
                    planets = {}
                results[dt][loc_key][str(hs)] = {
                    'meta': resp.get('meta', {}),
                    'planets': planets
                }

    out_json = OUT_DIR / 'house_system_sweep_results.json'
    out_txt = OUT_DIR / 'house_system_sweep_report.txt'
    with out_json.open('w', encoding='utf8') as f:
        json.dump({'generatedAt': datetime.utcnow().isoformat(), 'systems': systems, 'results': results}, f, indent=2)

    # produce human readable report
    with out_txt.open('w', encoding='utf8') as f:
        f.write(f"House system sweep report\nGenerated: {datetime.utcnow().isoformat()}\n\n")
        for dt, locs in results.items():
            f.write(f"DATETIME: {dt}\n")
            for loc_key, sysmap in locs.items():
                f.write(f"  LOCATION: {loc_key}\n")
                # for each pair of systems
                keys = list(sysmap.keys())
                for a,b in itertools.combinations(keys, 2):
                    aobj = sysmap[a]
                    bobj = sysmap[b]
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
                        f.write(f"    Differences between [{a}] and [{b}]:\n")
                        for d in diffs:
                            f.write(f"      {d}\n")
                f.write("\n")
            f.write("\n")

    print("WROTE", out_json)
    print("WROTE", out_txt)


if __name__ == '__main__':
    run()
