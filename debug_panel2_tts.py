#!/usr/bin/env python3
"""Enhanced test to debug the panel 2 TTS issue."""

import sys
import os
import re

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.chirp3hd_tts_service import Chirp3HDTTSService


def test_panel2_specific_cases():
    """Test specific cases that might be causing issues with panel 2."""
    tts_service = Chirp3HDTTSService()

    # Test cases that might be specific to panel 2
    panel2_cases = [
        # Common patterns that might appear
        'dialogue text: "The character realizes their inner strength."',
        "DIALOGUE TEXT: The character faces their greatest challenge.",
        'Dialogue Text: "Now is the moment of truth."',
        "dialogue_text: The inner journey begins here.",
        'DIALOGUE_TEXT: "Finding peace within the storm."',
        # Edge cases with different spacing
        'dialogue  text:   "Text with extra spaces"',
        'dialogue\ttext:\t"Text with tabs"',
        'dialogue text :"Text with space before colon"',
        "dialogue text: Text without quotes",
        # Cases with partial matches
        "This dialogue text: should not be cleaned",
        "Some dialogue text: in the middle should not be cleaned",
        # Cases that should be cleaned completely
        "dialogue text: ",  # Only prefix, no content
        'dialogue text:"',  # No space after colon
        'dialogue text:""',  # Empty quotes
    ]

    print("Testing Panel 2 specific TTS cases...")
    print("=" * 70)

    for i, test_text in enumerate(panel2_cases, 1):
        print(f"\nTest {i}:")
        print(f"  Input:  '{test_text}'")

        # Test the original regex pattern manually
        cleaned_manual = re.sub(
            r'^dialogue\s*text\s*:\s*["\']?', "", test_text, flags=re.IGNORECASE
        )
        print(f"  Manual: '{cleaned_manual}'")

        # Test with the service method
        cleaned_service = tts_service._clean_text_for_tts(test_text)
        print(f"  Service:'{cleaned_service}'")

        # Check if they match
        if cleaned_manual.strip("\"'").strip() != cleaned_service:
            print(f"  ⚠️  MISMATCH DETECTED!")
        else:
            print(f"  ✅ Match")


def test_edge_cases():
    """Test edge cases that might cause the TTS to say 'dialogue text'."""
    print("\n" + "=" * 70)
    print("Testing edge cases...")
    print("=" * 70)

    edge_cases = [
        # Text that contains "dialogue text" but not as prefix
        "The story shows dialogue text being processed",
        "We need to handle dialogue text properly",
        # Malformed patterns
        "dialogue textThe story begins",  # Missing colon
        "dialogue text The story begins",  # Missing colon with space
        "dialogue: text The story begins",  # Wrong colon placement
        # Multiple occurrences
        "dialogue text: The dialogue text should be clean",
        # Non-English characters or special cases
        'dialogue text: "The story with "nested quotes" continues"',
    ]

    tts_service = Chirp3HDTTSService()

    for i, test_text in enumerate(edge_cases, 1):
        print(f"\nEdge Case {i}:")
        print(f"  Input:  '{test_text}'")
        cleaned = tts_service._clean_text_for_tts(test_text)
        print(f"  Output: '{cleaned}'")

        # Check if "dialogue text" still appears in the output
        if "dialogue text" in cleaned.lower():
            print(f"  ⚠️  WARNING: 'dialogue text' still present in output!")


if __name__ == "__main__":
    test_panel2_specific_cases()
    test_edge_cases()
    print("\n✅ Enhanced TTS debugging completed!")
