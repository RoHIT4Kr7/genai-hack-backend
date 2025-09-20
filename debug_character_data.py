"""
Simple character data flow analysis - NO GENERATION, just data inspection
"""

from models.schemas import StoryInputs
from services.story_service import StoryService


def inspect_character_flow():
    """Check character data flow WITHOUT generating anything"""

    # Create test input with FEMALE character (Sneha)
    print("\n🔍 INSPECTING CHARACTER DATA FLOW")
    print("=" * 50)

    test_inputs = StoryInputs(
        # REQUIRED FIELDS from new schema
        mood="neutral",  # Using valid mood option
        coreValue="inner peace",
        supportSystem="meditation practice",
        nickname="Sneha",
        age="young-adult",
        gender="female",
        # Optional legacy fields
        vibe="calm",
        pastResilience="I have overcome anxiety before",
        innerDemon="I sometimes doubt my abilities",
        desiredOutcome="I want to feel more confident",
    )

    print(f"INPUT CHARACTER NAME (nickname): {test_inputs.nickname}")
    print(f"INPUT GENDER: {test_inputs.gender}")
    print(f"INPUT AGE: {test_inputs.age}")
    print(f"INPUT MOOD: {test_inputs.mood}")
    print(f"INPUT VIBE: {test_inputs.vibe}")

    # Initialize story service
    story_service = StoryService()

    # Check story planning method - this should NOT generate images
    print("\n📝 ANALYZING STORY PLANNING PHASE...")

    # Let's just inspect the story service methods without calling them
    print(
        f"Story service has generate_story_plan: {hasattr(story_service, 'generate_story_plan')}"
    )
    print(
        f"Story service has generate_streaming_story: {hasattr(story_service, 'generate_streaming_story')}"
    )

    print("\n✅ CHARACTER DATA INSPECTION COMPLETE")
    print("This test did NOT generate any images or stories")
    print("It only checked that our input data structure is correct")

    return test_inputs


if __name__ == "__main__":
    result = inspect_character_flow()
    print(f"\n🎯 Final result: {result.nickname} ({result.gender})")
