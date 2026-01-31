import requests
import sys

BASE_URL = "http://127.0.0.1:8081"

def test_auth_flow():
    # 1. Login (assuming a test user exists or we can register one)
    email = "test_auth_debug_8081@example.com"
    password = "password123"
    
    print(f"1. Registering/Logging in user: {email}")
    register_payload = {"email": email, "password": password, "full_name": "Debug User"}
    
    # Try register
    resp = requests.post(f"{BASE_URL}/calc/api/v1/auth/register", json=register_payload)
    if resp.status_code not in [200, 400]:
        print(f"Registration failed: {resp.status_code} {resp.text}")
        return

    # Login
    login_payload = {"email": email, "password": password}
    resp = requests.post(f"{BASE_URL}/calc/api/v1/auth/login", json=login_payload)
    
    if resp.status_code != 200:
        print(f"Login failed: {resp.status_code} {resp.text}")
        return
    
    token_data = resp.json()
    access_token = token_data["access_token"]
    print(f"Login successful. Access Token: {access_token[:20]}...")
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # 2. Call Protected Status Endpoint
    print("\n2. Calling Protected Endpoint: /calc/api/v1/deva/horoscope/status")
    resp = requests.get(f"{BASE_URL}/calc/api/v1/deva/horoscope/status", headers=headers)
    print(f"Status Code: {resp.status_code}")
    print(f"Response: {resp.text}")
    
    # 3. Call Chat History Endpoint (User reported failure here)
    print("\n3. Calling Protected Endpoint: /calc/api/v1/deva/chat/history")
    resp = requests.get(f"{BASE_URL}/calc/api/v1/deva/chat/history", headers=headers)
    print(f"Status Code: {resp.status_code}")
    print(f"Response: {resp.text}")

    if resp.status_code == 200:
        print("\nSUCCESS: Auth works locally on port 8081.")
    else:
        print("\nFAILURE: Auth failed locally on chat history.")

if __name__ == "__main__":
    try:
        test_auth_flow()
    except Exception as e:
        print(f"Test failed with error: {e}")
