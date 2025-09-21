"""
Test the sanitization function and verify CRLF removal
"""

import sys

sys.path.append(".")

try:
    from config.settings import _sanitize, settings

    # Test the sanitizer function
    test_cases = [
        "clean-id",
        "id-with-space ",
        " id-with-leading-space",
        "id-with-newline\n",
        "id-with-crlf\r\n",
        "id-with-both\r\nand-more\n",
        "\r\n\r\ncontaminated\r\n\r\n",
    ]

    print("🧪 Testing _sanitize function:")
    print("=" * 50)

    for i, test in enumerate(test_cases):
        result = _sanitize(test)
        print(f"Test {i+1}:")
        print(f"  Input:  {repr(test)}")
        print(f"  Output: {repr(result)}")
        print(
            f"  Clean:  {'✅' if '\\r' not in result and '\\n' not in result else '❌'}"
        )
        print()

    # Test the actual settings
    print("🔧 Testing actual settings:")
    print("=" * 50)
    print(f"Google Client ID: {repr(settings.google_client_id[:50])}...")
    print(f"Length: {len(settings.google_client_id)}")
    print(
        f"Has CRLF: {'❌' if '\\r' in settings.google_client_id or '\\n' in settings.google_client_id else '✅'}"
    )

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback

    traceback.print_exc()
