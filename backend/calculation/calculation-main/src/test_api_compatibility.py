import sys
import os

# Add local paths
src_dir = os.path.dirname(os.path.abspath(__file__))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from fastapi.testclient import TestClient
from api.app import app

def test_matching_endpoints():
    client = TestClient(app)
    
    print("=== TESTING GET /api/match/compatibility ===")
    response = client.get(
        "/api/match/compatibility",
        params={
            "boy_nakshatra": 13,
            "boy_pada": 1,
            "girl_nakshatra": 17,
            "girl_pada": 2,
            "method": "North"
        }
    )
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}\n")
    assert response.status_code == 200
    assert "Hasta" in response.json()["maleNakshatra"]
    
    print("=== TESTING POST /api/match/compatibility ===")
    post_data = {
        "maleNakshatra": "Hasta (Pada 1)",
        "femaleNakshatra": "Anuradha (Pada 2)",
        "system": "North"
    }
    response_post = client.post("/api/match/compatibility", json=post_data)
    print(f"Status Code: {response_post.status_code}")
    print(f"Response: {response_post.json()}\n")
    assert response_post.status_code == 200
    assert "Hasta" in response_post.json()["maleNakshatra"]

    print("=== TESTING POST WITH NUMERIC STRINGS ===")
    post_data_numeric = {
        "maleNakshatra": "13-1",
        "femaleNakshatra": "17 (Pada 2)",
        "system": "South"
    }
    response_post_num = client.post("/api/match/compatibility", json=post_data_numeric)
    print(f"Status Code: {response_post_num.status_code}")
    print(f"Response: {response_post_num.json()}\n")
    assert response_post_num.status_code == 200
    assert response_post_num.json()["maxScore"] == 10

    print("✅ All matching endpoint tests passed successfully!")

if __name__ == "__main__":
    test_matching_endpoints()
