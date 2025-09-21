#!/usr/bin/env python3
"""
Comprehensive authentication flow debugger to identify the Google OAuth issue
"""

import os
import json
import base64
import requests
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from config.settings import settings


def debug_google_client_id():
    """Debug the Google Client ID configuration"""
    print("=" * 60)
    print("🔍 DEBUGGING GOOGLE CLIENT ID")
    print("=" * 60)

    # Check environment variable
    env_client_id = os.getenv("GOOGLE_CLIENT_ID", "")
    print(f"[ENV] GOOGLE_CLIENT_ID: '{env_client_id}'")
    print(f"[ENV] Length: {len(env_client_id)}")
    print(f"[ENV] Repr: {repr(env_client_id)}")
    print(f"[ENV] Has \\r\\n: {'\\r\\n' in env_client_id}")

    # Check settings
    settings_client_id = settings.google_client_id
    print(f"[SETTINGS] google_client_id: '{settings_client_id}'")
    print(f"[SETTINGS] Length: {len(settings_client_id)}")
    print(f"[SETTINGS] Repr: {repr(settings_client_id)}")
    print(f"[SETTINGS] Has \\r\\n: {'\\r\\n' in settings_client_id}")

    # Check stripped version
    stripped_client_id = settings_client_id.strip()
    print(f"[STRIPPED] stripped: '{stripped_client_id}'")
    print(f"[STRIPPED] Length: {len(stripped_client_id)}")
    print(f"[STRIPPED] Repr: {repr(stripped_client_id)}")
    print(f"[STRIPPED] Has \\r\\n: {'\\r\\n' in stripped_client_id}")

    return stripped_client_id


def test_google_verification_behavior(client_id):
    """Test Google's id_token.verify_oauth2_token behavior"""
    print("\n" + "=" * 60)
    print("🧪 TESTING GOOGLE VERIFICATION BEHAVIOR")
    print("=" * 60)

    # Create a mock token for testing (this will fail but show us the error)
    fake_token = "eyJhbGciOiJSUzI1NiIsImtpZCI6IjMwYzE1N2U4ZDJkZmY1YTU4NDQ5ZjhlYWJlMDAwOGUyMjUzZWIyZjYiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJhY2NvdW50cy5nb29nbGUuY29tIiwiYXpwIjoiNjc0ODQ4Mzk1Nzk0LWpzZmV2ZjhpaWZ2bWpoMzNnbzNjdXFmOTZwMmxpZXRlLmFwcHMuZ29vZ2xldXNlcmNvbnRlbnQuY29tIiwiYXVkIjoiNjc0ODQ4Mzk1Nzk0LWpzZmV2ZjhpaWZ2bWpoMzNnbzNjdXFmOTZwMmxpZXRlLmFwcHMuZ29vZ2xldXNlcmNvbnRlbnQuY29tIiwic3ViIjoiMTAwMzM4NjE1ODY2MjEyNTA5NDc4IiwiZW1haWwiOiJ0ZXN0QGV4YW1wbGUuY29tIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsImF0X2hhc2giOiJ0ZXN0IiwibmFtZSI6IlRlc3QgVXNlciIsInBpY3R1cmUiOiJodHRwczovL3Rlc3QuY29tL3Rlc3QuanBnIiwiZ2l2ZW5fbmFtZSI6IlRlc3QiLCJmYW1pbHlfbmFtZSI6IlVzZXIiLCJsb2NhbGUiOiJlbiIsImlhdCI6MTYzMDAwMDAwMCwiZXhwIjoyMDAwMDAwMDAwfQ.fake_signature"

    try:
        result = id_token.verify_oauth2_token(
            fake_token, google_requests.Request(), client_id
        )
        print(f"[UNEXPECTED] Token verification succeeded: {result}")
    except ValueError as e:
        error_str = str(e)
        print(f"[EXPECTED] Verification failed: {error_str}")

        # Analyze the error message
        if "audience" in error_str.lower():
            print(f"[ANALYSIS] This is an audience error")
            if "\\r\\n" in error_str:
                print(f"[CRITICAL] Error contains \\r\\n characters!")
            if "expected one of" in error_str:
                # Extract the expected audience list from error
                try:
                    start = error_str.find("expected one of [")
                    if start != -1:
                        end = error_str.find("]", start)
                        if end != -1:
                            expected_part = error_str[start : end + 1]
                            print(f"[EXTRACTED] Expected part: {expected_part}")
                            print(f"[EXTRACTED] Repr: {repr(expected_part)}")
                except Exception as parse_error:
                    print(f"[ERROR] Could not parse expected audience: {parse_error}")

        return error_str
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        return str(e)


def test_manual_token_parsing():
    """Test our manual token parsing approach"""
    print("\n" + "=" * 60)
    print("🔧 TESTING MANUAL TOKEN PARSING")
    print("=" * 60)

    # Sample token payload for testing
    sample_payload = {
        "iss": "accounts.google.com",
        "azp": "674848395794-jsfevf8iifvmjh33go3cuqf96p2liete.apps.googleusercontent.com",
        "aud": "674848395794-jsfevf8iifvmjh33go3cuqf96p2liete.apps.googleusercontent.com",
        "sub": "100338615866212509478",
        "email": "test@example.com",
        "email_verified": True,
        "name": "Test User",
        "picture": "https://test.com/test.jpg",
        "iat": 1630000000,
        "exp": 2000000000,
    }

    # Encode the payload
    payload_json = json.dumps(sample_payload)
    payload_b64 = base64.urlsafe_b64encode(payload_json.encode()).decode().rstrip("=")

    print(f"[MANUAL] Sample payload: {payload_json}")
    print(f"[MANUAL] Base64 encoded: {payload_b64}")

    # Test decoding
    try:
        # Add padding
        payload_b64_padded = payload_b64 + "=" * (4 - len(payload_b64) % 4)
        decoded_payload = base64.urlsafe_b64decode(payload_b64_padded)
        parsed_payload = json.loads(decoded_payload)

        print(f"[MANUAL] Decoded successfully: {parsed_payload}")
        print(f"[MANUAL] Audience from token: '{parsed_payload.get('aud', '')}'")

        return parsed_payload
    except Exception as e:
        print(f"[MANUAL] Failed to decode: {e}")
        return None


def main():
    """Run comprehensive authentication debugging"""
    print("🚀 Starting comprehensive authentication flow debugging")
    print(f"📅 Timestamp: {json.dumps({'timestamp': 'now'})}")

    # Step 1: Debug Google Client ID
    client_id = debug_google_client_id()

    # Step 2: Test Google verification behavior
    test_google_verification_behavior(client_id)

    # Step 3: Test manual token parsing
    test_manual_token_parsing()

    # Step 4: Recommendations
    print("\n" + "=" * 60)
    print("💡 RECOMMENDATIONS")
    print("=" * 60)

    if "\\r\\n" in client_id:
        print("❌ CRITICAL: Client ID contains \\r\\n characters")
        print("   ✅ FIX: Clean the Secret Manager value")
    else:
        print("✅ Client ID appears clean")

    print("\n🔍 Next steps:")
    print("1. Run this script on the deployed Cloud Run instance")
    print("2. Compare frontend Google Client ID with backend")
    print("3. Test with real Google ID token from frontend")
    print("4. Check if Google's library has internal formatting issues")


if __name__ == "__main__":
    main()
