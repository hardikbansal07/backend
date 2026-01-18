import requests
import json
import logging

logging.basicConfig(level=logging.INFO)

url = "http://localhost:8000/calc/api/v1/auth/guest-login"

payload = {
    "date_of_birth": "1990-01-01",
    "time_of_birth": "12:00",
    "place_of_birth": "New Delhi, India",
    "latitude": 28.61,
    "longitude": 77.20,
    "preferred_language": "English"
}

try:
    print(f"Testing {url}...")
    response = requests.post(url, json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        data = response.json()
        if "access_token" in data and data.get("user", {}).get("is_guest"):
            print("SUCCESS: Guest login working locally!")
        else:
            print("FAILURE: Invalid response format")
    else:
        print("FAILURE: Non-200 status code")

except Exception as e:
    print(f"ERROR: {e}")
