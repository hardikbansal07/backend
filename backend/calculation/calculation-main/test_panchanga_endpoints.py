import requests
import json

BASE_URL = 'http://localhost:8080'

# Step 1: Create horoscope
print('Creating horoscope...')
horoscope_data = {
    'birthDateTime': '2001-03-07T16:20:00',
    'location': {
        'place': 'Delhi',
        'latitude': 28.6139,
        'longitude': 77.2090,
        'tzOffset': 5.5
    }
}

response = requests.post(f'{BASE_URL}/api/horoscope', json=horoscope_data)
print(f'Horoscope Status: {response.status_code}')

if response.status_code == 200:
    request_id = response.json().get('requestId')
    print(f'Request ID: {request_id}\n')
    
    # Step 2: Test Panchanga
    print('Testing /api/panchanga...')
    try:
        pan_response = requests.get(f'{BASE_URL}/api/panchanga', params={'request_id': request_id})
        print(f'Panchanga Status: {pan_response.status_code}')
        if pan_response.status_code == 200:
            print('✅ Panchanga works!')
            print(json.dumps(pan_response.json(), indent=2)[:500])
        else:
            print(f'❌ Error: {pan_response.text}')
    except Exception as e:
        print(f'❌ Exception: {e}')
    
    # Step 3: Test Transit
    print('\nTesting /api/transit...')
    try:
        transit_response = requests.get(f'{BASE_URL}/api/transit', params={'request_id': request_id})
        print(f'Transit Status: {transit_response.status_code}')
        if transit_response.status_code == 200:
            print('✅ Transit works!')
            print(f'Found {len(transit_response.json().get("planets", []))} planets')
        else:
            print(f'❌ Error: {transit_response.text}')
    except Exception as e:
        print(f'❌ Exception: {e}')
