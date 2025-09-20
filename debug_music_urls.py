#!/usr/bin/env python3
"""
Test script to debug dhyaan service music URL generation
"""

import asyncio
import json
from pathlib import Path

# Add the parent directory to Python path to import services
import sys

sys.path.append(str(Path(__file__).parent))

from services.dhyaan_service import dhyaan_service


async def test_music_url_generation():
    """Test music URL generation for different feeling combinations"""

    test_combinations = [
        ("anxious", "peaceful"),
        ("sad", "joy"),
        ("lonely", "love"),
        ("stressed", "calm"),  # This might not exist in metadata
    ]

    print("🎵 Testing Music URL Generation")
    print("=" * 50)

    for current_feeling, desired_feeling in test_combinations:
        print(f"\n🔍 Testing: {current_feeling} → {desired_feeling}")

        # Test music info retrieval
        music_info = dhyaan_service._get_music_info(current_feeling, desired_feeling)
        print(f"  📝 Music Info: {json.dumps(music_info, indent=4)}")

        # Test background music URL generation
        try:
            if music_info["gcs_path"]:
                background_url = await dhyaan_service._get_background_music_url(
                    music_info["gcs_path"]
                )
                print(f"  🔗 Background URL Generated: {len(background_url) > 0}")
                print(
                    f"  🔗 URL Preview: {background_url[:100]}..."
                    if background_url
                    else "  ❌ No URL generated"
                )
            else:
                print("  ❌ No GCS path found")
        except Exception as e:
            print(f"  ❌ Error generating URL: {e}")

        print("-" * 30)


if __name__ == "__main__":
    if dhyaan_service is None:
        print("❌ DhyaanService is not initialized")
        exit(1)

    print("✅ DhyaanService is initialized")
    asyncio.run(test_music_url_generation())
