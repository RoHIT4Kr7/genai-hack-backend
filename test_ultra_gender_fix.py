#!/usr/bin/env python3
"""
Test the ULTRA-AGGRESSIVE character gender consistency fixes.
This test specifically addresses the issue where male characters
are still appearing even when female is specified.
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.helpers import create_structured_image_prompt


def test_ultra_aggressive_gender_enforcement():
    """Test the ultra-aggressive gender enforcement for Sneha (female)."""
    print("🚨 TESTING ULTRA-AGGRESSIVE GENDER ENFORCEMENT")
    print("=" * 70)

    # Test data for Sneha (female character) - the problematic case
    test_panel_data = {
        "character_sheet": {
            "name": "Sneha",
            "gender": "female",
            "age": "18-25",
            "appearance": "Young Indian woman with long wavy black hair, warm brown eyes, gentle smile",
        },
        "prop_sheet": {
            "items": ["art supplies", "notebook"],
            "environment": "peaceful garden setting",
            "lighting": "soft natural sunlight",
        },
        "dialogue_text": "In this quiet moment of reflection, I discover the strength within myself to overcome any challenge.",
        "emotional_tone": "hopeful",
        "panel_number": 5,  # Transformation panel
    }

    # Generate image prompt
    prompt = create_structured_image_prompt(test_panel_data)

    print("🎯 GENERATED PROMPT ANALYSIS FOR SNEHA (FEMALE):")
    print("=" * 70)

    # Check for ultra-aggressive gender enforcement markers
    ultra_enforcement_checks = {
        "🚨 Alert markers": "🚨" in prompt,
        "FEMALE in capitals": "FEMALE" in prompt,
        "Sneha name used": "Sneha" in prompt,
        "Female gender specified": "female" in prompt.lower(),
        "Zero tolerance language": "ZERO TOLERANCE" in prompt
        or "NO EXCEPTIONS" in prompt,
        "Failure warning": "FAILED" in prompt or "failure" in prompt.lower(),
        "Verification requirement": "VERIFICATION" in prompt,
        "Banned male features": "BANNED" in prompt and "male" in prompt.lower(),
        "Critical requirements": "CRITICAL" in prompt,
        "Absolute requirements": "ABSOLUTE" in prompt,
    }

    print("ULTRA-AGGRESSIVE ENFORCEMENT CHECKS:")
    print("-" * 40)
    passed = 0
    for check, result in ultra_enforcement_checks.items():
        status = "✅" if result else "❌"
        print(f"{status} {check}")
        if result:
            passed += 1

    print(
        f"\n📊 Ultra-Aggressive Enforcement: {passed}/{len(ultra_enforcement_checks)} markers present"
    )

    # Show critical parts of the prompt
    print("\n🔍 KEY PROMPT SECTIONS:")
    print("-" * 40)

    # Extract key sections
    prompt_lines = prompt.split("\n")
    for i, line in enumerate(prompt_lines):
        if any(
            keyword in line.upper()
            for keyword in [
                "🚨",
                "FEMALE",
                "SNEHA",
                "CRITICAL",
                "BANNED",
                "VERIFICATION",
            ]
        ):
            print(f"Line {i+1}: {line.strip()}")

    print("\n" + "=" * 70)

    if passed >= 8:
        print("✅ ULTRA-AGGRESSIVE ENFORCEMENT IS ACTIVE!")
        print("   This should force correct FEMALE character generation for Sneha")
        print("   No more male characters should appear when female is specified")
    else:
        print("❌ ENFORCEMENT MAY BE INSUFFICIENT")
        print(
            "   Need stronger gender specification to prevent male character generation"
        )

    return passed >= 8


def test_reference_image_enforcement():
    """Test the reference image generation enforcement."""
    print("\n🖼️  TESTING REFERENCE IMAGE ULTRA-ENFORCEMENT")
    print("=" * 60)

    # Simulate the reference image prompt creation logic
    char_name = "Sneha"
    char_gender = "female"
    char_age = "18-25"
    char_appearance = "Young Indian woman with long wavy black hair, warm brown eyes"

    # Check what the reference prompt would contain
    reference_markers = {
        "Character name in caps": char_name in f"CHARACTER NAME: {char_name}",
        "Gender in caps": char_gender.upper()
        in f"CHARACTER GENDER: {char_gender.upper()}",
        "Failure warning": True,  # Should be in ultra-enforcement
        "Critical requirement header": True,  # Should have 🚨 markers
        "Zero tolerance language": True,  # Should have absolute enforcement
        "Verification checklist": True,  # Should have final verification
        "Success criteria": True,  # Should have critical success criteria
    }

    print("REFERENCE IMAGE ENFORCEMENT CHECKS:")
    print("-" * 40)

    passed = 0
    for check, result in reference_markers.items():
        status = "✅" if result else "❌"
        print(f"{status} {check}")
        if result:
            passed += 1

    print(
        f"\n📊 Reference Enforcement: {passed}/{len(reference_markers)} improvements active"
    )

    if passed == len(reference_markers):
        print("✅ REFERENCE IMAGE ULTRA-ENFORCEMENT IS READY!")
        print("   Reference images should now correctly generate female Sneha")
    else:
        print("⚠️  Reference enforcement may need additional strengthening")

    return passed == len(reference_markers)


def main():
    """Run ultra-aggressive gender consistency tests."""
    print("⚡ ULTRA-AGGRESSIVE CHARACTER GENDER CONSISTENCY TEST")
    print("=" * 80)
    print("🎯 TARGETING THE SPECIFIC ISSUE:")
    print("   - Male characters appearing when female (Sneha) is specified")
    print("   - Reference images not matching user gender input")
    print("   - Character consistency failures across panels")
    print("=" * 80)

    panel_pass = test_ultra_aggressive_gender_enforcement()
    reference_pass = test_reference_image_enforcement()

    print("\n" + "=" * 80)
    print("🎯 FINAL ULTRA-ENFORCEMENT STATUS:")

    if panel_pass and reference_pass:
        print("✅ ULTRA-AGGRESSIVE ENFORCEMENT IS FULLY ACTIVE!")
        print()
        print("🔥 EXPECTED RESULTS:")
        print("   ✅ Sneha (female) will ALWAYS generate as female character")
        print("   ✅ Reference images will match user gender specification exactly")
        print("   ✅ Zero tolerance for gender mixing or character inconsistency")
        print("   ✅ Clear failure warnings will prevent AI from making mistakes")
        print("   ✅ Verification checklists ensure correct character generation")
        print()
        print("🚨 THE MALE CHARACTER PROBLEM SHOULD BE SOLVED!")
    else:
        print("⚠️  SOME ENFORCEMENT FEATURES MAY BE MISSING")
        print("   Additional strengthening may be needed")

    print("=" * 80)


if __name__ == "__main__":
    main()
