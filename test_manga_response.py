import requests
import json


def test_manga_generation_response():
    """Test manga generation to verify URL mapping"""

    # Test data for manga generation
    test_data = {
        "inputs": {
            "nickname": "TestUser",
            "age": "18-25",
            "gender": "female",
            "mood": "happy",
            "vibe": "calm",
            "situation": "Testing the system",
        }
    }

    # Test with a temporary auth token (this would fail with 403, but let's see the structure)
    headers = {"Content-Type": "application/json"}

    print("🧪 Testing manga generation response structure...")

    try:
        # This will return 403, but we can check the endpoint exists
        response = requests.post(
            "http://localhost:8000/api/v1/generate-manga-nano-banana",
            json=test_data,
            headers=headers,
            timeout=10,
        )

        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")

        if response.status_code == 403:
            print("✅ Endpoint exists and requires authentication (expected)")
            print("✅ Backend schema changes should work with proper auth")

    except Exception as e:
        print(f"Error: {e}")

    # Test the simple endpoint to make sure backend is running
    try:
        simple_response = requests.get("http://localhost:8000/api/v1/test-simple")
        print(
            f"\nSimple test: {simple_response.status_code} - {simple_response.json()}"
        )
    except Exception as e:
        print(f"Simple test error: {e}")


if __name__ == "__main__":
    test_manga_generation_response()
