#!/usr/bin/env python3
"""
Deep diagnostic test to trace where male characters are coming from
when female (Sneha) is specified in the first two slides.
"""

import sys
import os
import asyncio

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.story_service import story_service
from models.schemas import StoryInputs
from loguru import logger


async def test_character_data_flow():
    """Test the complete flow from StoryInputs to panel generation to see where gender gets lost."""
    print("🔍 DEEP CHARACTER DATA FLOW ANALYSIS")
    print("=" * 80)

    # Create test inputs with Sneha (female)
    test_inputs = StoryInputs(
        nickname="Sneha",
        gender="female",
        age="18-25",
        currentMood="anxious",
        specificWorries="feeling overwhelmed with studies",
        personalityTraits=["creative", "sensitive"],
        lifeDream="become a successful artist",
        recentExperience="failed an important exam",
        preferredArt="manga",
        preferredLength="6-panel",
    )

    print("📝 INPUT DATA:")
    print(f"   Nickname: {test_inputs.nickname}")
    print(f"   Gender: {test_inputs.gender}")
    print(f"   Age: {test_inputs.age}")
    print()

    # Step 1: Generate story plan
    print("📚 STEP 1: STORY PLANNING")
    print("-" * 40)

    panels = await story_service.generate_story_plan(test_inputs)

    print(f"Generated {len(panels)} panels")
    for i, panel in enumerate(panels[:2]):  # Check first 2 panels where issue occurs
        character_sheet = panel.get("character_sheet", {})
        print(f"\nPanel {i+1} Character Data:")
        print(f"   Name: {character_sheet.get('name', 'NOT FOUND')}")
        print(f"   Gender: {character_sheet.get('gender', 'NOT FOUND')}")
        print(f"   Age: {character_sheet.get('age', 'NOT FOUND')}")
        print(
            f"   Appearance: {character_sheet.get('appearance', 'NOT FOUND')[:100]}..."
        )

        # Check if the character data has correct gender
        if character_sheet.get("gender", "").lower() != "female":
            print(
                f"   🚨 PROBLEM FOUND: Gender is '{character_sheet.get('gender')}' instead of 'female'!"
            )
        else:
            print("   ✅ Gender is correctly set to female")

    print()

    # Step 2: Test prompt generation for first two panels
    print("🎨 STEP 2: PROMPT GENERATION ANALYSIS")
    print("-" * 40)

    from utils.helpers import create_structured_image_prompt

    for i, panel in enumerate(panels[:2]):
        print(f"\nPanel {i+1} Prompt Analysis:")

        # Add panel number to panel data
        panel_with_number = panel.copy()
        panel_with_number["panel_number"] = i + 1

        # Generate the prompt
        prompt = create_structured_image_prompt(panel_with_number)

        # Analyze the prompt for gender enforcement
        gender_markers = {
            "🚨 Alert markers": "🚨" in prompt,
            "Sneha name": "Sneha" in prompt,
            "FEMALE in caps": "FEMALE" in prompt,
            "Female lowercase": "female" in prompt.lower(),
            "Male banned": "BANNED" in prompt and "male" in prompt.lower(),
            "Zero tolerance": "ZERO TOLERANCE" in prompt,
            "Completely failed": "COMPLETELY FAILED" in prompt,
        }

        print(f"   Gender Enforcement Markers:")
        for marker, found in gender_markers.items():
            status = "✅" if found else "❌"
            print(f"     {status} {marker}")

        # Show key parts of prompt
        prompt_lines = prompt.split("\n")
        critical_lines = []
        for line in prompt_lines:
            if any(
                keyword in line.upper()
                for keyword in ["🚨", "SNEHA", "FEMALE", "GENDER", "CHARACTER"]
            ):
                critical_lines.append(line.strip())

        print(f"   Critical Prompt Lines:")
        for line in critical_lines[:5]:  # Show first 5 critical lines
            print(f"     > {line}")

        if len(critical_lines) > 5:
            print(f"     ... and {len(critical_lines) - 5} more lines")

    print()

    # Step 3: Test reference image generation
    print("🖼️  STEP 3: REFERENCE IMAGE ANALYSIS")
    print("-" * 40)

    if panels:
        story_context = {
            "character_sheet": panels[0].get("character_sheet", {}),
            "prop_sheet": panels[0].get("prop_sheet", {}),
            "style_guide": panels[0].get("style_guide", {}),
        }

        char_data = story_context["character_sheet"]
        print("Reference Image Character Data:")
        print(f"   Name: {char_data.get('name', 'NOT FOUND')}")
        print(f"   Gender: {char_data.get('gender', 'NOT FOUND')}")
        print(f"   Age: {char_data.get('age', 'NOT FOUND')}")

        if char_data.get("gender", "").lower() != "female":
            print(
                f"   🚨 REFERENCE PROBLEM: Gender is '{char_data.get('gender')}' not 'female'!"
            )
            print(
                "   This could create male reference images that override panel prompts!"
            )
        else:
            print("   ✅ Reference character data has correct female gender")

    print("\n" + "=" * 80)
    print("🎯 DIAGNOSTIC SUMMARY:")
    print("If character data shows correct 'female' gender but images are still male,")
    print("the issue is likely in the AI model not respecting the prompts.")
    print("If character data shows wrong gender, the issue is in story planning.")
    print("=" * 80)


async def main():
    """Run the complete diagnostic test."""
    await test_character_data_flow()


if __name__ == "__main__":
    asyncio.run(main())
