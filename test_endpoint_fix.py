#!/usr/bin/env python3
"""
Quick test to verify the API endpoint path is working correctly
"""
import requests
import json


def test_api_endpoint():
    """Test the manga generation endpoint directly"""
    print("🧪 Testing API Endpoint Path Fix")
    print("=" * 40)

    # Test data
    test_payload = {
        "inputs": {
            "nickname": "TestUser",
            "age": "18-25",
            "gender": "female",
            "mood": "happy",
            "vibe": "calm",
            "situation": "testing the endpoint path fix",
        }
    }

    # Test the correct path (without double /api/v1)
    correct_url = "http://localhost:8000/api/v1/generate-manga-nano-banana"

    print(f"🌐 Testing URL: {correct_url}")

    try:
        response = requests.post(correct_url, json=test_payload, timeout=5)

        print(f"📡 Status Code: {response.status_code}")

        if response.status_code == 404:
            print("❌ 404 Error - endpoint not found")
            print("   This suggests the backend is not running")
        elif response.status_code == 403:
            print("✅ 403 Error - endpoint found but requires authentication")
            print("   This means the path fix worked!")
        elif response.status_code == 422:
            print("✅ 422 Error - endpoint found but validation failed")
            print("   This means the path fix worked!")
        else:
            print(f"📊 Response: {response.text[:200]}")

    except requests.ConnectionError:
        print("❌ Connection Error - backend server is not running")
    except Exception as e:
        print(f"❌ Error: {e}")

    # Also test the wrong path that was causing the issue
    wrong_url = "http://localhost:8000/api/v1/api/v1/generate-manga-nano-banana"

    print(f"\n🔍 Testing wrong URL (should be 404): {wrong_url}")

    try:
        response = requests.post(wrong_url, json=test_payload, timeout=5)
        print(f"📡 Status Code: {response.status_code}")

        if response.status_code == 404:
            print("✅ Correctly returns 404 for wrong path")
        else:
            print(f"⚠️  Unexpected response: {response.status_code}")

    except requests.ConnectionError:
        print("❌ Connection Error - backend server is not running")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    test_api_endpoint()
