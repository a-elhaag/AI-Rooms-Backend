import json

import requests

BASE_URL = "http://localhost:8000"


def test_translate():
    print("\n--- Testing Translation Endpoint ---")
    url = f"{BASE_URL}/ai/translate"
    payload = {"text": "Hello, how are you doing today?", "target_language": "es"}
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print("✅ Success!")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"❌ Failed: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ Error: {e}")


def test_summarize():
    print("\n--- Testing Summarize Endpoint ---")
    url = f"{BASE_URL}/ai/summarize-room"
    payload = {"room_id": "test_room_123", "last_n_messages": 5}
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print("✅ Success!")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"❌ Failed: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    print("Testing FastAPI AI Endpoints...")
    test_translate()
    test_summarize()
