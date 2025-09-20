#!/usr/bin/env python3
"""Test script specifically for panel 2 dialogue text scenarios."""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.chirp3hd_tts_service import Chirp3HDTTSService


def test_panel_2_scenarios():
    """Test typical panel 2 scenarios that might have the underscore pattern."""
    tts_service = Chirp3HDTTSService()

    # These are the types of patterns that might appear specifically for panel 2
    panel2_scenarios = [
        # Most likely culprits - these are probably what's causing the issue
        'dialogue_text: "Maya faces her creative challenge."',
        'DIALOGUE_TEXT: "The moment of truth arrives."',
        "dialogue_text: Maya realizes she must trust herself.",
        'DIALOGUE_TEXT: "With trembling hands, she reaches for her courage."',
        # Also test the space variations to make sure they still work
        'dialogue text: "Maya faces her creative challenge."',
        'DIALOGUE TEXT: "The moment of truth arrives."',
        "dialogue text: Maya realizes she must trust herself.",
        'DIALOGUE TEXT: "With trembling hands, she reaches for her courage."',
        # Mixed underscore and space patterns
        'dialogue_text : "Maya finds her inner strength."',
        'dialogue _text: "The challenge becomes clear."',
        'dialogue_ text: "Maya steps forward with confidence."',
    ]

    print("Testing Panel 2 specific scenarios...")
    print("=" * 60)

    for i, scenario in enumerate(panel2_scenarios, 1):
        print(f"\nScenario {i}:")
        print(f"  Input:  '{scenario}'")

        cleaned = tts_service._clean_text_for_tts(scenario)
        print(f"  Output: '{cleaned}'")

        # Check if the prefix was properly removed
        if any(
            pattern in cleaned.lower()
            for pattern in ["dialogue_text:", "dialogue text:"]
        ):
            print(f"  ❌ ERROR: Prefix not properly removed!")
        else:
            print(f"  ✅ SUCCESS: Prefix properly removed")


if __name__ == "__main__":
    test_panel_2_scenarios()
    print("\n🎉 Panel 2 TTS test completed!")
