#!/usr/bin/env python3
"""
Test script for DhyaanService status in GCloud Run environment
"""

import json
import requests
from datetime import datetime

# Your hosted backend URL
BACKEND_URL = "https://manga-wellness-backend-rsijjqxv6a-uc.a.run.app"


def test_dhyaan_service():
    """Test the dhyaan service endpoints."""
    print("🧘 Testing DhyaanService in GCloud Run...")
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("-" * 60)

    # Test general health endpoint
    try:
        print("1. Testing general health endpoint...")
        health_response = requests.get(f"{BACKEND_URL}/api/v1/health", timeout=10)
        print(f"General Health Status: {health_response.status_code}")
        if health_response.status_code == 200:
            health_data = health_response.json()
            print(f"General Health: {json.dumps(health_data, indent=2)}")
        print()
    except Exception as e:
        print(f"General Health Check Failed: {e}")
        print()

    # Test dhyaan-specific test endpoint
    try:
        print("2. Testing dhyaan test endpoint...")
        dhyaan_test_response = requests.get(
            f"{BACKEND_URL}/api/v1/dhyaan-test", timeout=10
        )
        print(f"Dhyaan Test Status: {dhyaan_test_response.status_code}")
        if dhyaan_test_response.status_code == 200:
            dhyaan_test_data = dhyaan_test_response.json()
            print(f"Dhyaan Test: {json.dumps(dhyaan_test_data, indent=2)}")
        else:
            print(f"Dhyaan Test Error: {dhyaan_test_response.text}")
        print()
    except Exception as e:
        print(f"Dhyaan Test Failed: {e}")
        print()

    # Test dhyaan health endpoint
    try:
        print("3. Testing dhyaan health endpoint...")
        dhyaan_health_response = requests.get(
            f"{BACKEND_URL}/api/v1/health", timeout=10
        )
        print(f"Dhyaan Health Status: {dhyaan_health_response.status_code}")
        print()
    except Exception as e:
        print(f"Dhyaan Health Check Failed: {e}")
        print()

    print("-" * 60)
    print("✅ Service status check completed!")


if __name__ == "__main__":
    test_dhyaan_service()
