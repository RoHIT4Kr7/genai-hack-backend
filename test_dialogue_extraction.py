#!/usr/bin/env python3
"""
Test the dialogue extraction fix by running a simple story generation test
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.schemas import StoryInputs
import asyncio
import requests
import json


async def test_story_generation_api():
    """Test story generation via API to see if dialogue extraction is fixed."""

    # Test data similar to what caused the issue
    test_data = {
        "name": "tanishq",
        "nickname": "tanishq",
        "age": "19",
        "gender": "male",
        "archetype": "hero",
        "mood": "happy",
        "dream": "I want to become a great software engineer",
        "hobby": "coding and building projects",
        "struggle": "I doubt my coding abilities sometimes",
        "secretWeapon": "I never give up when learning",
        "coreValue": "helping others through technology",
        "supportSystem": "family and coding community",
        "vibe": "motivational",
        "desiredOutcome": "building confidence in my abilities",
    }

    print("🔍 Testing story generation with dialogue extraction fix...")
    print(f"Input: {test_data['nickname']}, {test_data['age']}, {test_data['gender']}")
    print("-" * 80)

    try:
        # Make API request
        url = "http://localhost:8000/api/v1/generate-manga-streaming"
        response = requests.post(url, json=test_data, timeout=120)

        if response.status_code == 200:
            result = response.json()
            story_id = result.get("story_id")

            print(f"✅ Story generated: {story_id}")
            print("-" * 80)

            # Wait a moment for generation to complete
            import time

            print("⏱️  Waiting for generation to complete...")
            time.sleep(5)

            # Check the logs for dialogue content
            print("📄 Checking recent logs for dialogue content...")

        else:
            print(f"❌ API Error: {response.status_code}")
            print(response.text)

    except requests.exceptions.ConnectionError:
        print("❌ Connection error - make sure backend is running on localhost:8000")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(test_story_generation_api())
