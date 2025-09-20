"""
Debug script to test story generation and dialogue extraction.
"""

import asyncio
from models.schemas import StoryInputs
from services.story_service import story_service


async def test_story_generation():
    """Test story generation and check dialogue extraction."""

    # Create test inputs representing the user's issue
    inputs = StoryInputs(
        nickname="Alex",
        age="18-25",
        gender="Female",
        mood="happy",
        supportSystem="family",
        coreValue="kindness",
        pastResilience="helped friend through tough times",
        innerDemon="self-doubt",
        desiredOutcome="feel confident and inspired",
        secretWeapon="creative problem solving",
    )

    print("🧪 Testing Story Generation & Dialogue Extraction")
    print(f"User: {inputs.nickname} ({inputs.gender}, {inputs.age})")
    print(f"Mood: {inputs.mood}")
    print(f"Goal: {inputs.desiredOutcome}")
    print("-" * 50)

    try:
        # Test story plan generation
        print("📝 Generating story plan...")
        panels = await story_service.generate_story_plan(inputs)

        print(f"✅ Generated {len(panels)} panels")
        print("-" * 50)

        for i, panel in enumerate(panels, 1):
            dialogue = panel.get("dialogue_text", "NO DIALOGUE FOUND")
            character_name = panel.get("character_sheet", {}).get("name", "NO NAME")

            print(f"PANEL {i}:")
            print(f"  Character: {character_name}")
            print(f'  Dialogue: "{dialogue}"')
            print(f"  Length: {len(dialogue) if dialogue else 0} chars")
            print(f"  Word count: {len(dialogue.split()) if dialogue else 0} words")

            # Check if dialogue is meaningful or generic
            if dialogue and len(dialogue) > 10:
                if "meanwhile continuing forward" in dialogue.lower():
                    print("  ⚠️  CONTAINS FALLBACK TEXT!")
                else:
                    print("  ✅ Contains meaningful content")
            else:
                print("  ❌ Empty or too short")

            print()

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_story_generation())
