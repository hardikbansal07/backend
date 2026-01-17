import json, sys, time
import httpx

BASE = 'http://127.0.0.1:8080'

def main():
    client = httpx.Client(timeout=30.0)
    summary = {}
    # 1. Health
    r = client.get(f'{BASE}/api/health'); summary['health']=r.json()
    # 2. Create horoscope
    body = {
        "birthDateTime": "2000-01-01T06:30:00",
        "location": {"tzOffset":5.5, "place":"Chennai,IN", "latitude":13.08, "longitude":80.27},
        "divisionalFactors":[1,9,10],
        "sendToAgent": False,
        "sendToAgentMode":"summary"
    }
    r = client.post(f'{BASE}/api/horoscope', json=body); r.raise_for_status(); h = r.json(); summary['create_keys']= list(h.keys()); rid = h['meta']['requestId']
    # 3. Fetch components
    def grab(path, name):
        resp = client.get(f'{BASE}{path}', params={'request_id': rid}) if '{rid}' not in path else client.get(f"{BASE}{path.format(rid=rid)}")
        if resp.status_code != 200:
            summary[name] = f'ERR {resp.status_code}'
        else:
            data = resp.json() if 'json' in resp.headers.get('content-type','') else resp.text
            if isinstance(data, dict):
                summary[name] = list(data.keys())[:8]
            else:
                summary[name] = f'string {len(data)} chars'
    grab('/api/yogas','yogas_keys')
    grab('/api/strength','strength_keys')
    grab('/api/deepstrength','deep_strength_keys')
    grab('/api/summary','summary_keys')
    grab('/api/aspects','aspects_keys')
    grab('/api/panchanga','panchanga_keys')
    grab('/api/transit','transit_keys')
    # Bundle
    r = client.get(f'{BASE}/api/bundle', params={'request_id': rid, 'includeSummary': True}); summary['bundle_keys']= list(r.json().keys())
    # Agent relay (will likely be skipped without webhook URL)
    r = client.post(f'{BASE}/api/agent/relay', json={'requestId': rid}); summary['agent_relay']=r.status_code
    time.sleep(0.2)
    ev = client.get(f'{BASE}/api/agent/events', params={'limit':5}).json().get('events',[])
    summary['agent_events_count']= len([e for e in ev if e.get('requestId')==rid])

    print(json.dumps(summary, indent=2))

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print('SMOKE_TEST_ERROR', e)
        sys.exit(1)
