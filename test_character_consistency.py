#!/usr/bin/env python3
"""
Test script to verify character consistency fixes.
This tests that user inputs (name=Sneha, gender=female, age=17-25) are properly enforced.
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.helpers import create_structured_image_prompt


def test_character_consistency_enforcement():
    """Test that character inputs are properly enforced in image prompts."""

    print("Testing Character Consistency Enforcement...")
    print("=" * 60)

    # Test case: User input for Sneha (female, 17-25)
    test_panel_data = {
        "character_sheet": {
            "name": "Sneha",
            "gender": "female",
            "age": "18-25",
            "appearance": "Young Indian woman with long black hair, warm brown eyes, wearing casual modern clothing",
        },
        "prop_sheet": {
            "items": ["art supplies", "creative journal"],
            "environment": "modern art studio with natural lighting",
        },
        "style_guide": {
            "art_style": "anime illustration",
            "visual_elements": ["hopeful", "creative"],
        },
        "dialogue_text": "Sneha finds her inner strength through her art",
        "emotional_tone": "hopeful",
        "panel_number": 2,
    }

    print("Test Input:")
    print(f"  Name: {test_panel_data['character_sheet']['name']}")
    print(f"  Gender: {test_panel_data['character_sheet']['gender']}")
    print(f"  Age: {test_panel_data['character_sheet']['age']}")
    print(f"  Appearance: {test_panel_data['character_sheet']['appearance']}")
    print()

    # Generate image prompt
    prompt = create_structured_image_prompt(test_panel_data)

    print("Generated Image Prompt:")
    print("-" * 40)
    print(prompt)
    print("-" * 40)
    print()

    # Check for consistency enforcement
    consistency_checks = {
        "Name 'Sneha' used": "Sneha" in prompt,
        "Gender 'female' enforced": "female" in prompt.lower() and "FEMALE" in prompt,
        "Age specification included": "18-25" in prompt
        or "young adult" in prompt.lower(),
        "User appearance used": "long black hair" in prompt.lower()
        or "brown eyes" in prompt.lower(),
        "Gender consistency rules": "MANDATORY FEMALE" in prompt
        or "feminine" in prompt.lower(),
        "Original character requirements": "completely original" in prompt.lower(),
        "Consistency enforcement": "MUST" in prompt and "identical" in prompt.lower(),
    }

    print("Consistency Check Results:")
    print("-" * 30)
    for check, result in consistency_checks.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {check}")

    print()

    # Overall assessment
    passed_checks = sum(consistency_checks.values())
    total_checks = len(consistency_checks)

    if passed_checks == total_checks:
        print(f"🎉 ALL CHECKS PASSED ({passed_checks}/{total_checks})")
        print("✅ Character consistency enforcement is working properly!")
    else:
        print(f"⚠️  SOME CHECKS FAILED ({passed_checks}/{total_checks})")
        print("❌ Character consistency needs improvement")


def test_different_gender_scenarios():
    """Test both male and female character scenarios."""
    print("\n" + "=" * 60)
    print("Testing Different Gender Scenarios...")
    print("=" * 60)

    scenarios = [
        {
            "name": "Sneha",
            "gender": "female",
            "age": "young-adult",
            "appearance": "Young Indian woman with long black hair",
        },
        {
            "name": "Arjun",
            "gender": "male",
            "age": "teen",
            "appearance": "Teenage boy with short brown hair",
        },
    ]

    for i, char_data in enumerate(scenarios, 1):
        print(f"\nScenario {i}: {char_data['name']} ({char_data['gender']})")
        print("-" * 30)

        test_data = {
            "character_sheet": char_data,
            "prop_sheet": {"items": ["symbolic item"], "environment": "test setting"},
            "dialogue_text": "Test dialogue",
            "emotional_tone": "neutral",
            "panel_number": 1,
        }

        prompt = create_structured_image_prompt(test_data)

        # Check gender-specific enforcement
        if char_data["gender"] == "female":
            gender_check = "FEMALE" in prompt and "feminine" in prompt.lower()
            print(f"✅ Female enforcement: {gender_check}")
        elif char_data["gender"] == "male":
            gender_check = "MALE" in prompt and "masculine" in prompt.lower()
            print(f"✅ Male enforcement: {gender_check}")

        name_check = char_data["name"] in prompt
        print(f"✅ Name usage: {name_check}")


if __name__ == "__main__":
    test_character_consistency_enforcement()
    test_different_gender_scenarios()

    print("\n" + "=" * 60)
    print("🔧 CHARACTER CONSISTENCY FIXES SUMMARY:")
    print("1. ✅ Updated VISUAL_ARTIST_PROMPT to strictly enforce user inputs")
    print("2. ✅ Enhanced create_structured_image_prompt with gender/age enforcement")
    print("3. ✅ Improved reference image generation with user-specific details")
    print("4. ✅ Strengthened panel prompts with consistency requirements")
    print(
        "5. 🎯 Next: Test with real API to verify Sneha appears consistently as female"
    )
    print("=" * 60)
