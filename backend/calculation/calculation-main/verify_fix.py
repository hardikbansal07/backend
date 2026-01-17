import requests
import json
import sys

def verify():
    try:
        with open('test_payload.json', 'r') as f:
            payload = json.load(f)
        
        print("Sending request to http://localhost:8080/api/horoscope...")
        resp = requests.post('http://localhost:8080/api/horoscope', json=payload)
        
        if resp.status_code != 200:
            print(f"Error: {resp.status_code} - {resp.text}")
            sys.exit(1)
            
        data = resp.json()
        
        # Check D1
        d1 = data.get('rasiChart')
        print("\n--- D1 (Rasi) ---")
        print(f"Sign: {d1.get('ascendantSign')}")
        print(f"Sign Number: {d1.get('ascendantSignNumber')}")
        print(f"Longitude: {d1.get('ascendantLongitudeDMS')}")
        asc_d1_planet = next((p for p in d1.get('planets', []) if 'Ascendant' in p['name']), None)
        if asc_d1_planet:
             print(f"Ascendant Planet Row: {asc_d1_planet['name']} in {asc_d1_planet['sign']} (HouseAbs: {asc_d1_planet['houseAbs']}) deg: {asc_d1_planet['longitudeDMS']}")

        # Check D9
        d9 = next((c for c in data.get('divisionalCharts', []) if c['factor'] == 9), None)
        if not d9:
            print("\nError: D9 chart not found in response")
            sys.exit(1)

        print("\n--- D9 (Navamsa) ---")
        print(f"Sign: {d9.get('ascendantSign')}")
        print(f"Sign Number: {d9.get('ascendantSignNumber')}")
        print(f"Longitude: {d9.get('ascendantLongitudeDMS')}")
        asc_d9_planet = next((p for p in d9.get('planets', []) if 'Ascendant' in p['name']), None)
        if asc_d9_planet:
             print(f"Ascendant Planet Row: {asc_d9_planet['name']} in {asc_d9_planet['sign']} (HouseAbs: {asc_d9_planet['houseAbs']}) deg: {asc_d9_planet['longitudeDMS']}")

        # Comparison
        if d1.get('ascendantSignNumber') == d9.get('ascendantSignNumber') and \
           d1.get('ascendantLongitudeDMS') == d9.get('ascendantLongitudeDMS'):
             print("\nFAIL: D1 and D9 Ascendants are IDENTICAL. Bug not fixed.")
             sys.exit(1)
        else:
             print("\nSUCCESS: D1 and D9 Ascendants are DIFFERENT.")

    except Exception as e:
        print(f"Exception: {e}")
        sys.exit(1)

if __name__ == "__main__":
    verify()
