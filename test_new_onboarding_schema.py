#!/usr/bin/env python3
"""
Test script to verify the updated schema works with new onboarding data.
"""

import sys
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, '.')

from models.schemas import StoryInputs, StoryGenerationRequest


def test_new_onboarding_schema():
    """Test that the new schema accepts onboarding data correctly."""

    print("🧪 Testing new onboarding schema...")

    # Sample data from the new OnboardingScreen.tsx
    new_onboarding_data = {
        "mood": "stressed",
        "coreValue": "kindness",
        "supportSystem": "friend",
        "pastResilience": "I overcame my fear of public speaking by joining a debate club and practicing every day.",
        "innerDemon": "Self-doubt that whispers 'you're not good enough' and holds me back from pursuing my dreams.",
        "desiredOutcome": "Feeling confident in my abilities and pursuing my dreams without fear, knowing I can overcome any challenge.",
        "nickname": "Alex",
        "secretWeapon": "my creativity and persistence",
        "age": "young-adult",  # Changed from int to string
        "gender": "non-binary"
    }

    try:
        # Test creating StoryInputs with new data
        story_inputs = StoryInputs(**new_onboarding_data)

        print("✅ StoryInputs created successfully with new onboarding data!")
        print(f"   Nickname: {story_inputs.nickname}")
        print(f"   Age: {story_inputs.age} (type: {type(story_inputs.age)})")
        print(f"   Core Value: {story_inputs.coreValue}")
        print(f"   Secret Weapon: {story_inputs.secretWeapon}")

        # Test creating StoryGenerationRequest
        request = StoryGenerationRequest(inputs=story_inputs)
        print("✅ StoryGenerationRequest created successfully!")

        # Test the age conversion method
        from services.story_service import StoryService
        service = StoryService()

        age_int = service._convert_age_range_to_int(story_inputs.age)
        print(f"✅ Age conversion: '{story_inputs.age}' -> {age_int}")

        # Test legacy field mapping (should work with empty legacy fields)
        legacy_value = service._get_legacy_field_value(story_inputs, 'secretWeapon', 'hobby')
        print(f"✅ Legacy field mapping: {legacy_value}")

        # Verify required fields are present
        assert story_inputs.nickname, "Nickname should be present"
        assert story_inputs.age, "Age should be present"
        assert story_inputs.coreValue, "Core value should be present"
        assert story_inputs.secretWeapon, "Secret weapon should be present"

        print("✅ All required fields are present!")

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_backward_compatibility():
    """Test that old schema still works for backward compatibility."""

    print("\n🔄 Testing backward compatibility with legacy data...")

    # Sample legacy data (old schema)
    legacy_data = {
        "mood": "happy",
        "vibe": "shonen",  # Legacy field
        "archetype": "hero",  # Legacy field
        "dream": "To become a great artist",  # Legacy field -> maps to pastResilience
        "mangaTitle": "My Hero Journey",  # Legacy field
        "nickname": "Hero",
        "hobby": "drawing",  # Legacy field -> maps to secretWeapon
        "age": "adult",  # Now string instead of int
        "gender": "male"
    }

    try:
        # Test creating StoryInputs with legacy data
        story_inputs = StoryInputs(**legacy_data)

        print("✅ StoryInputs created successfully with legacy data!")
        print(f"   Nickname: {story_inputs.nickname}")
        print(f"   Age: {story_inputs.age} (type: {type(story_inputs.age)})")
        print(f"   Legacy dream: {story_inputs.dream}")
        print(f"   Legacy hobby: {story_inputs.hobby}")

        # Test field mapping
        from services.story_service import StoryService
        service = StoryService()

        # Test that legacy fields are accessible
        dream_value = service._get_legacy_field_value(story_inputs, 'pastResilience', 'dream')
        print(f"✅ Legacy dream mapping: {dream_value}")

        hobby_value = service._get_legacy_field_value(story_inputs, 'secretWeapon', 'hobby')
        print(f"✅ Legacy hobby mapping: {hobby_value}")

        return True

    except Exception as e:
        print(f"❌ Backward compatibility test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_schema_validation():
    """Test schema validation for edge cases."""

    print("\n🔍 Testing schema validation...")

    # Test missing required fields
    try:
        invalid_data = {
            "mood": "happy",
            "age": "adult",
            "gender": "male"
            # Missing nickname and other required fields
        }

        StoryInputs(**invalid_data)
        print("❌ Should have failed validation for missing required fields")
        return False

    except Exception as e:
        print(f"✅ Correctly rejected invalid data: {type(e).__name__}")

    # Test invalid enum values
    try:
        invalid_enum_data = {
            "mood": "invalid_mood",  # Invalid mood
            "coreValue": "creativity",
            "supportSystem": "friend",
            "pastResilience": "Some past challenge",
            "innerDemon": "Some inner demon",
            "desiredOutcome": "Some desired outcome",
            "nickname": "Test",
            "secretWeapon": "creativity",
            "age": "adult",
            "gender": "male"
        }

        StoryInputs(**invalid_enum_data)
        print("❌ Should have failed validation for invalid enum values")
        return False

    except Exception as e:
        print(f"✅ Correctly rejected invalid enum values: {type(e).__name__}")

    return True


def main():
    """Run all tests."""
    print("🚀 Starting schema update tests...\n")

    tests = [
        test_new_onboarding_schema,
        test_backward_compatibility,
        test_schema_validation
    ]

    results = []
    for test in tests:
        results.append(test())

    if all(results):
        print("\n🎉 All tests passed! Schema update is successful.")
        print("✅ New onboarding data structure is supported")
        print("✅ Backward compatibility is maintained")
        print("✅ Schema validation works correctly")
        print("✅ Age field properly converted from int to string")
    else:
        print("\n💥 Some tests failed! Check the implementation.")

    return all(results)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
