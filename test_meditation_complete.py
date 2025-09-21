#!/usr/bin/env python3
"""
Complete test of the meditation generation flow with the updated GCS fixes
"""

import requests
import time
import json

# Configuration
BASE_URL = "https://manga-wellness-backend-rsijjqxv6a-uc.a.run.app"
EMAIL = "test@example.com"
PASSWORD = "testpassword123"


def authenticate():
    """Get an auth token"""
    auth_data = {"email": EMAIL, "password": PASSWORD}

    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=auth_data)
        print(f"Auth response status: {response.status_code}")
        print(f"Auth response body: {response.text}")

        if response.status_code == 200:
            data = response.json()
            return data.get("access_token")
        else:
            print("Creating new user...")
            register_response = requests.post(
                f"{BASE_URL}/auth/register", json=auth_data
            )
            print(f"Register status: {register_response.status_code}")

            if register_response.status_code == 201:
                # Try login again
                response = requests.post(f"{BASE_URL}/auth/login", json=auth_data)
                if response.status_code == 200:
                    data = response.json()
                    return data.get("access_token")
    except Exception as e:
        print(f"Auth error: {e}")

    return None


def test_meditation_generation(token):
    """Test the complete meditation generation flow"""
    if not token:
        print("❌ No auth token available")
        return

    headers = {"Authorization": f"Bearer {token}"}

    # Request meditation generation
    meditation_request = {
        "theme": "stress relief after work",
        "duration_minutes": 3,
        "voice_style": "calm_female",
        "background_music": True,
    }

    print("\n📋 Testing meditation generation...")
    print(f"Request: {json.dumps(meditation_request, indent=2)}")

    try:
        response = requests.post(
            f"{BASE_URL}/dhyaan/generate-meditation",
            json=meditation_request,
            headers=headers,
            timeout=180,  # 3 minute timeout
        )

        print(f"\n✅ Response Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Meditation Generated Successfully!")
            print(f"📱 Response data keys: {list(data.keys())}")

            if "audio_url" in data:
                print(f"🎵 Audio URL: {data['audio_url']}")
            if "script" in data:
                print(f"📝 Script length: {len(data.get('script', ''))}")
            if "theme" in data:
                print(f"🎯 Theme: {data['theme']}")
            if "duration" in data:
                print(f"⏱️  Duration: {data['duration']} minutes")

            # Test if audio URL is accessible
            if "audio_url" in data and data["audio_url"]:
                print(f"\n🎵 Testing audio URL accessibility...")
                try:
                    audio_response = requests.head(data["audio_url"], timeout=10)
                    print(f"Audio URL status: {audio_response.status_code}")
                    if audio_response.status_code == 200:
                        print(f"✅ Audio is accessible!")
                    else:
                        print(
                            f"❌ Audio URL not accessible: {audio_response.status_code}"
                        )
                except Exception as e:
                    print(f"❌ Audio URL test failed: {e}")

        elif response.status_code == 400:
            print(f"❌ Bad Request (400)")
            print(f"Response: {response.text}")
        elif response.status_code == 422:
            print(f"❌ Validation Error (422)")
            print(f"Response: {response.text}")
        else:
            print(f"❌ Unexpected status: {response.status_code}")
            print(f"Response: {response.text}")

    except requests.exceptions.Timeout:
        print("❌ Request timed out (3 minutes)")
    except Exception as e:
        print(f"❌ Error during meditation generation: {e}")


def main():
    print("🧘 Testing Complete Meditation Generation Flow")
    print(f"🌐 Backend URL: {BASE_URL}")

    # Test dhyaan service directly first
    test_dhyaan_service_direct()

    # Try meditation generation without auth
    test_meditation_generation_direct()


def test_dhyaan_service_direct():
    """Test dhyaan service health without auth"""
    print("\n🧘 Testing dhyaan service health...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/dhyaan-test")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
        else:
            print(f"Response text: {response.text}")
    except Exception as e:
        print(f"Error: {e}")


def test_meditation_generation_direct():
    """Test meditation generation without auth (if possible)"""
    print("\n📋 Testing meditation generation directly...")

    # Request meditation generation
    meditation_request = {
        "theme": "stress relief after work",
        "duration_minutes": 2,
        "voice_style": "calm_female",
        "background_music": True,
    }

    print(f"Request: {json.dumps(meditation_request, indent=2)}")

    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/dhyaan/generate-meditation",
            json=meditation_request,
            timeout=180,  # 3 minute timeout
        )

        print(f"\n✅ Response Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Meditation Generated Successfully!")
            print(f"📱 Response data keys: {list(data.keys())}")

            if "audio_url" in data:
                print(f"🎵 Audio URL: {data['audio_url']}")
            if "script" in data:
                print(f"📝 Script length: {len(data.get('script', ''))}")
            if "theme" in data:
                print(f"🎯 Theme: {data['theme']}")
            if "duration" in data:
                print(f"⏱️  Duration: {data['duration']} minutes")

            # Test if audio URL is accessible
            if "audio_url" in data and data["audio_url"]:
                print(f"\n🎵 Testing audio URL accessibility...")
                try:
                    audio_response = requests.head(data["audio_url"], timeout=10)
                    print(f"Audio URL status: {audio_response.status_code}")
                    if audio_response.status_code == 200:
                        print(f"✅ Audio is accessible!")

                        # Try to get first few bytes to confirm
                        partial_response = requests.get(
                            data["audio_url"],
                            headers={"Range": "bytes=0-1023"},
                            timeout=10,
                        )
                        if partial_response.status_code in [200, 206]:
                            print(
                                f"✅ Audio content verified (got {len(partial_response.content)} bytes)"
                            )

                    else:
                        print(
                            f"❌ Audio URL not accessible: {audio_response.status_code}"
                        )
                except Exception as e:
                    print(f"❌ Audio URL test failed: {e}")

        elif response.status_code == 401:
            print(f"❌ Authentication required (401)")
            print(f"Response: {response.text}")
        elif response.status_code == 400:
            print(f"❌ Bad Request (400)")
            print(f"Response: {response.text}")
        elif response.status_code == 422:
            print(f"❌ Validation Error (422)")
            print(f"Response: {response.text}")
        else:
            print(f"❌ Unexpected status: {response.status_code}")
            print(f"Response: {response.text}")

    except requests.exceptions.Timeout:
        print("❌ Request timed out (3 minutes)")
    except Exception as e:
        print(f"❌ Error during meditation generation: {e}")


if __name__ == "__main__":
    main()
