"""
Quick test script to debug Google Client ID issue
"""

import os
import sys
import base64
import json

# Add current directory to path
sys.path.append(".")

try:
    from config.settings import settings

    print("✅ Successfully imported settings")

    # Test 1: Check environment variable
    env_client_id = os.getenv("GOOGLE_CLIENT_ID", "NOT_SET")
    print(f"[ENV] GOOGLE_CLIENT_ID: '{env_client_id}'")
    print(f"[ENV] Length: {len(env_client_id)}")
    print(f"[ENV] Repr: {repr(env_client_id)}")

    # Test 2: Check settings value
    settings_client_id = settings.google_client_id
    print(f"[SETTINGS] google_client_id: '{settings_client_id}'")
    print(f"[SETTINGS] Length: {len(settings_client_id)}")
    print(f"[SETTINGS] Repr: {repr(settings_client_id)}")

    # Test 3: Check for whitespace issues
    stripped = settings_client_id.strip()
    print(f"[STRIPPED] After strip(): '{stripped}'")
    print(f"[STRIPPED] Length: {len(stripped)}")
    print(f"[STRIPPED] Has \\r\\n: {'\\r\\n' in stripped}")

    # Test 4: Expected client ID for comparison
    expected = (
        "674848395794-jsfevf8iifvmjh33go3cuqf96p2liete.apps.googleusercontent.com"
    )
    print(f"[EXPECTED] Expected: '{expected}'")
    print(f"[MATCH] Settings matches expected: {stripped == expected}")

    # Test 5: Simulate the Google verification error
    if stripped:
        mock_error = (
            f"Token has wrong audience {expected}, expected one of ['{stripped}\\r\\n']"
        )
        print(f"[SIMULATION] Mock error: {mock_error}")
        print(f"[SIMULATION] Contains \\r\\n: {'\\r\\n' in mock_error}")

except Exception as e:
    print(f"❌ Error importing or testing: {e}")
    import traceback

    traceback.print_exc()
