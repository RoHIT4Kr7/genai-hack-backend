#!/usr/bin/env python3
"""
Test script for DhyaanService in GCloud Run environment
"""

import os
import json
import asyncio
import requests
from datetime import datetime

# Your hosted backend URL
BACKEND_URL = "https://manga-wellness-backend-674848395794.us-central1.run.app"


async def test_dhyaan_service():
    """Test the dhyaan service endpoint."""
    print("🧘 Testing DhyaanService in GCloud Run...")
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("-" * 60)

    # Test health endpoint first
    try:
        print("1. Testing health endpoint...")
        health_response = requests.get(f"{BACKEND_URL}/api/v1/health", timeout=10)
        print(f"Health Status: {health_response.status_code}")
        if health_response.status_code == 200:
            health_data = health_response.json()
            print(f"Health Response: {json.dumps(health_data, indent=2)}")
        else:
            print(f"Health Error: {health_response.text}")
        print()
    except Exception as e:
        print(f"Health Check Failed: {e}")
        print()

    # Test dhyaan generation endpoint
    try:
        print("2. Testing meditation generation...")
        meditation_request = {
            "current_feeling": "anxious",
            "desired_feeling": "peaceful",
            "experience": "beginner",
        }

        print(f"Request: {json.dumps(meditation_request, indent=2)}")

        # Make request to generate meditation
        response = requests.post(
            f"{BACKEND_URL}/api/v1/generate-meditation",
            json=meditation_request,
            timeout=120,  # 2 minutes timeout for generation
            headers={"Content-Type": "application/json"},
        )

        print(f"Response Status: {response.status_code}")

        if response.status_code == 200:
            meditation_data = response.json()
            print("✅ Meditation generated successfully!")

            # Print key information
            print(f"Meditation ID: {meditation_data.get('meditation_id', 'N/A')}")
            print(f"Title: {meditation_data.get('title', 'N/A')}")
            print(f"Duration: {meditation_data.get('duration', 'N/A')} seconds")
            print(
                f"Audio URL available: {'Yes' if meditation_data.get('audio_url') else 'No'}"
            )
            print(
                f"Background Music URL available: {'Yes' if meditation_data.get('background_music_url') else 'No'}"
            )
            print(f"Script length: {len(meditation_data.get('script', ''))} characters")

        else:
            print(f"❌ Meditation generation failed!")
            print(f"Error: {response.text}")

    except Exception as e:
        print(f"❌ Meditation generation request failed: {e}")

    print("-" * 60)
    print("Test completed!")


if __name__ == "__main__":
    asyncio.run(test_dhyaan_service())
