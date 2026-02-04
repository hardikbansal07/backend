import urllib.request
import urllib.error
import json
import random
import string
import sys

BASE_URL = "http://localhost:8000"

def get_random_string(length=8):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))

def make_request(endpoint, method="POST", data=None, headers=None):
    url = f"{BASE_URL}{endpoint}"
    if headers is None:
        headers = {}
    
    headers["Content-Type"] = "application/json"
    
    json_data = json.dumps(data).encode("utf-8") if data else None
    
    req = urllib.request.Request(url, data=json_data, headers=headers, method=method)
    
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.read().decode('utf-8')}")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def test_memory():
    print("=== Testing Chat Memory ===")
    
    # 1. Register User
    email = f"test_{get_random_string()}@example.com"
    password = "password123"
    print(f"1. Registering user: {email}")
    
    reg_data = {
        "email": email,
        "password": password,
        "full_name": "Test User"
    }
    
    reg_response = make_request("/calc/api/v1/auth/register", data=reg_data)
    if not reg_response:
        print("Registration failed.")
        return
    
    # 2. Login
    print("2. Logging in...")
    login_data = {
        "email": email,
        "password": password
    }
    login_response = make_request("/calc/api/v1/auth/login", data=login_data)
    if not login_response or "access_token" not in login_response:
        print("Login failed.")
        return
        
    token = login_response["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("   Logged in successfully.")
    
    # 3. Chat 1: Provide Details
    print("\n3. Sending Message 1: Providing DOB (1990-05-20)...")
    chat_data_1 = {
        "question": "My name is Alex and my date of birth is 1990-05-20."
    }
    resp1 = make_request("/calc/api/v1/deva/chat", data=chat_data_1, headers=headers)
    if resp1:
        print(f"   AI Response: {resp1.get('response')[:100]}...")
    
    # 4. Chat 2: Ask follow-up
    print("\n4. Sending Message 2: Asking for DOB (testing memory)...")
    chat_data_2 = {
        "question": "What is the date of birth I just told you?"
    }
    resp2 = make_request("/calc/api/v1/deva/chat", data=chat_data_2, headers=headers)
    
    if resp2:
        response_text = resp2.get('response', '')
        print(f"   AI Response: {response_text}")
        
        if "1990" in response_text or "May 20" in response_text or "20-05" in response_text:
            print("\n✅ SUCCESS: AI remembered the date of birth!")
        else:
            print("\n❌ FAILURE: AI did not mention the date of birth.")
    else:
        print("Failed to get response for second message.")

if __name__ == "__main__":
    test_memory()
