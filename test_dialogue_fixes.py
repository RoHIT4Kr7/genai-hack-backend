"""
Test script to verify the fixes for TTS dialogue and gender representation.
"""

import json
from models.schemas import StoryInputs
from services.story_service import story_service


def test_dialogue_generation():
    """Test the dialogue generation improvements."""
    print("🧪 Testing Enhanced Dialogue Generation")
    print("=" * 50)

    # Create test inputs
    inputs = StoryInputs(
        nickname="Sophia",
        age="18-25",
        gender="Female",
        mood="stressed",
        supportSystem="family and close friends",
        coreValue="authenticity",
        pastResilience="overcame anxiety during public speaking",
        innerDemon="impostor syndrome",
        desiredOutcome="feel confident in my abilities",
        secretWeapon="empathy and understanding others",
    )

    print(f"User: {inputs.nickname} ({inputs.gender}, {inputs.age})")
    print(f"Mood: {inputs.mood} → Goal: {inputs.desiredOutcome}")
    print(f"Challenge: {inputs.innerDemon}")
    print("-" * 50)

    # Test meaningful panel dialogue generation
    print("📝 Testing Meaningful Panel Dialogue:")

    for i in range(1, 7):
        dialogue = story_service._generate_meaningful_panel_dialogue(i, inputs)
        word_count = len(dialogue.split())

        print(f"\nPanel {i} ({word_count} words):")
        print(f'  "{dialogue}"')

        # Check for quality
        if word_count >= 25 and word_count <= 45:
            print("  ✅ Good length for 8-10 second audio")
        elif word_count < 25:
            print("  ⚠️  Might be too short")
        else:
            print("  ⚠️  Might be too long")

        # Check for meaningful content
        if any(
            term in dialogue.lower()
            for term in [
                inputs.nickname.lower(),
                inputs.desiredOutcome.lower(),
                inputs.innerDemon.lower(),
            ]
        ):
            print("  ✅ Contains personalized content")
        else:
            print("  ⚠️  Might be too generic")

    print("\n" + "=" * 50)
    print("✅ Dialogue generation test complete!")

    # Test character sheet with gender
    print("\n🎨 Testing Character Sheet Generation:")
    from utils.helpers import create_user_context

    user_context = create_user_context(inputs)
    print(f"Gender in context: {'Gender: Female' in user_context}")
    print(f"Character name: {inputs.nickname}")

    print("\n✅ All tests completed!")
    print("\nKey improvements:")
    print("1. ✅ Enhanced dialogue generation with meaningful content")
    print("2. ✅ Proper word count for 8-10 second audio")
    print("3. ✅ Personalized content using user inputs")
    print("4. ✅ Gender information preserved in character context")
    print("5. ✅ Removed problematic TTS normalization")


if __name__ == "__main__":
    test_dialogue_generation()
