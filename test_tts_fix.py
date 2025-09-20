#!/usr/bin/env python3
"""Test script to verify the TTS cleaning fix."""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.chirp3hd_tts_service import Chirp3HDTTSService


def test_tts_cleaning():
    """Test that the TTS cleaning removes 'dialogue text: ' prefix."""
    tts_service = Chirp3HDTTSService()

    # Test cases with dialogue text prefix
    test_cases = [
        'dialogue text: "Sneha realizes now that her empathy, her kindness, was always her truest guide."',
        "dialogue text: Sneha realizes now that her empathy, her kindness, was always her truest guide.",
        'Dialogue Text: "With kindness as her compass, sneha chooses to walk this path with an open heart."',
        "DIALOGUE TEXT: With kindness as her compass, sneha chooses to walk this path with an open heart.",
        '"Sneha realizes now that her empathy, her kindness, was always her truest guide."',  # No prefix
        "Sneha realizes now that her empathy, her kindness, was always her truest guide.",  # No prefix
    ]

    print("Testing TTS text cleaning...")
    print("=" * 60)

    for i, test_text in enumerate(test_cases, 1):
        cleaned = tts_service._clean_text_for_tts(test_text)
        print(f"Test {i}:")
        print(f"  Input:  '{test_text}'")
        print(f"  Output: '{cleaned}'")
        print()

    print("✅ TTS cleaning test completed!")


if __name__ == "__main__":
    test_tts_cleaning()
