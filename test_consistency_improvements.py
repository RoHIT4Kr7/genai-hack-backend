#!/usr/bin/env python3
"""Test script to demonstrate the improved character consistency features."""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.helpers import (
    create_structured_image_prompt,
    _create_character_consistency_anchor,
)


def test_character_consistency():
    """Test the enhanced character consistency features."""

    # Sample character data that might be generated
    sample_character_sheet = {
        "name": "Maya",
        "age": "young adult",
        "gender": "female",
        "appearance": "oval face with warm brown eyes, shoulder-length wavy black hair with subtle highlights, fair skin tone, athletic build of medium height, wearing a casual blue denim jacket over a white t-shirt with comfortable dark jeans and white sneakers",
        "personality": "determined and hopeful with a gentle spirit",
        "goals": "to overcome anxiety and pursue art",
        "fears": "fear of judgment and failure",
        "strengths": "creative problem-solving and empathy",
    }

    sample_prop_sheet = {
        "items": [
            "art supplies and sketchbook",
            "anxiety as dark clouds",
            "creativity as golden light",
        ],
        "environment": "cozy art studio with natural lighting and inspiring artwork",
        "lighting": "warm natural light from large windows with soft shadows",
        "mood_elements": ["artistic inspiration", "supportive friends", "inner peace"],
    }

    sample_style_guide = {
        "art_style": "clean anime illustration with vibrant colors",
        "color_palette": "warm and inspiring tones",
        "visual_elements": ["gentle lighting", "creative atmosphere"],
    }

    # Test data for different panels
    test_panels = [
        {
            "character_sheet": sample_character_sheet,
            "prop_sheet": sample_prop_sheet,
            "style_guide": sample_style_guide,
            "dialogue_text": "Maya sits in her art studio, feeling overwhelmed by her perfectionist tendencies.",
            "emotional_tone": "contemplative",
            "panel_number": 1,
            "user_mood": "stressed",
            "user_vibe": "artistic",
        },
        {
            "character_sheet": sample_character_sheet,
            "prop_sheet": sample_prop_sheet,
            "style_guide": sample_style_guide,
            "dialogue_text": "Maya faces a blank canvas, feeling the weight of creative block.",
            "emotional_tone": "frustrated",
            "panel_number": 2,
            "user_mood": "stressed",
            "user_vibe": "artistic",
        },
        {
            "character_sheet": sample_character_sheet,
            "prop_sheet": sample_prop_sheet,
            "style_guide": sample_style_guide,
            "dialogue_text": "Maya remembers her past artistic achievements and finds inner strength.",
            "emotional_tone": "hopeful",
            "panel_number": 6,
            "user_mood": "happy",
            "user_vibe": "artistic",
        },
    ]

    print("=== CHARACTER CONSISTENCY TEST ===")
    print("\n1. Testing Character Consistency Anchor:")
    print("=" * 50)
    anchor = _create_character_consistency_anchor(sample_character_sheet)
    print(anchor)

    print("\n\n2. Testing Image Prompts for Different Panels:")
    print("=" * 50)

    for i, panel_data in enumerate(test_panels):
        print(f"\n--- PANEL {panel_data['panel_number']} ---")
        prompt = create_structured_image_prompt(panel_data)

        # Extract key consistency sections
        lines = prompt.split("\n")
        print("CONSISTENCY FEATURES FOUND:")

        in_consistency_section = False
        consistency_lines = []

        for line in lines:
            if (
                "CRITICAL CHARACTER CONSISTENCY" in line
                or "CONSISTENT VISUAL IDENTITY" in line
            ):
                in_consistency_section = True
                consistency_lines.append(line)
            elif in_consistency_section:
                if (
                    line.startswith("**")
                    and "CONSISTENT" not in line
                    and "Character" not in line
                    and "Same" not in line
                ):
                    break
                consistency_lines.append(line)

        for line in consistency_lines[:10]:  # Show first 10 consistency lines
            print(f"  {line}")

        print(f"\n  PROMPT LENGTH: {len(prompt)} characters")
        print(
            f"  CONSISTENCY KEYWORDS: {prompt.count('EXACT')} 'EXACT', {prompt.count('IDENTICAL')} 'IDENTICAL', {prompt.count('SAME')} 'SAME'"
        )

    print("\n\n3. Key Improvements Made:")
    print("=" * 50)
    improvements = [
        "✅ Added detailed character consistency anchor with physical descriptions",
        "✅ Enforced IDENTICAL character features across all panels",
        "✅ Added explicit restrictions against character transformations",
        "✅ Created consistent prop descriptions with visual continuity",
        "✅ Added environment progression that maintains location consistency",
        "✅ Enhanced Story Architect prompt for extremely detailed character descriptions",
        "✅ Added multiple consistency check keywords (EXACT, IDENTICAL, SAME)",
        "✅ Prohibited costume changes and appearance variations",
        "✅ Created panel-specific environment evolution while maintaining consistency",
    ]

    for improvement in improvements:
        print(improvement)

    print("\n4. Expected Results:")
    print("=" * 50)
    expected_results = [
        "🎯 Same character face, hair, and clothing in all 6 panels",
        "🎯 Props remain visually consistent when they appear",
        "🎯 Environment evolves logically but maintains the same location/style",
        "🎯 No fairy transformations or drastic appearance changes",
        "🎯 Character personality shows through consistent body language",
        "🎯 Motivational story arc that helps user overcome their specific struggle",
    ]

    for result in expected_results:
        print(result)


if __name__ == "__main__":
    test_character_consistency()
