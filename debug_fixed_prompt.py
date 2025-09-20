"""
Test the FIXED prompt construction to verify user context is properly inserted
"""

from models.schemas import StoryInputs
from utils.helpers import STORY_ARCHITECT_PROMPT


def test_fixed_prompt_formatting():
    """Test the CORRECTED prompt construction"""

    print("🔍 TESTING FIXED PROMPT CONSTRUCTION")
    print("=" * 60)

    # Create test inputs
    test_inputs = StoryInputs(
        mood="neutral",
        coreValue="inner peace",
        supportSystem="meditation practice",
        nickname="Sneha",
        age="young-adult",
        gender="female",
        vibe="calm",
    )

    # Recreate the NEW/FIXED prompt construction
    input_context = f"""
            User Inputs:
            - Mood: {test_inputs.mood}
            - Vibe: {test_inputs.vibe}
            - Archetype: {test_inputs.archetype}
            - Dream: {test_inputs.dream}
            - Manga Title: {test_inputs.mangaTitle}
            - Nickname: {test_inputs.nickname}
            - Hobby: {test_inputs.hobby}
            - Age: {test_inputs.age}
            - Gender: {test_inputs.gender}

            Please create a complete 6-panel manga story structure following the Story Architect guidelines.
            """

    print("📝 INPUT CONTEXT:")
    print(input_context)

    # Show the FIXED prompt construction
    full_prompt = STORY_ARCHITECT_PROMPT.format(user_context=input_context)

    print("\n⚡ FIXED PROMPT CONSTRUCTION:")
    print("Method: STORY_ARCHITECT_PROMPT.format(user_context=input_context)")
    print(f"Total length: {len(full_prompt)} characters")

    # Check that {user_context} placeholder is now filled
    if "{user_context}" in full_prompt:
        print(
            "❌ PROBLEM: {user_context} placeholder still exists - not properly filled!"
        )
    else:
        print(
            "✅ SUCCESS: {user_context} placeholder has been replaced with actual user data!"
        )

    # Check if the user's gender appears WITHIN the CHARACTER_SHEET section now
    character_sheet_start = full_prompt.find("CHARACTER_SHEET:")
    character_sheet_end = full_prompt.find("PROP_SHEET:")

    if character_sheet_start != -1 and character_sheet_end != -1:
        character_sheet_section = full_prompt[character_sheet_start:character_sheet_end]
        print("\n🎭 CHARACTER_SHEET SECTION CHECK:")

        if f"Gender: {test_inputs.gender}" in character_sheet_section:
            print(
                f"✅ User's gender '{test_inputs.gender}' is NOW in the CHARACTER_SHEET section!"
            )
        else:
            print(
                f"❌ User's gender '{test_inputs.gender}' still not in CHARACTER_SHEET section"
            )

        if f"Nickname: {test_inputs.nickname}" in character_sheet_section:
            print(
                f"✅ User's nickname '{test_inputs.nickname}' is NOW in the CHARACTER_SHEET section!"
            )
        else:
            print(
                f"❌ User's nickname '{test_inputs.nickname}' still not in CHARACTER_SHEET section"
            )

    # Show a snippet around where the user context should now be
    user_context_position = full_prompt.find("User Inputs:")
    if user_context_position != -1:
        snippet_start = max(0, user_context_position - 100)
        snippet_end = min(len(full_prompt), user_context_position + 400)
        print(f"\n📍 USER DATA POSITIONING (around position {user_context_position}):")
        print("..." + full_prompt[snippet_start:snippet_end] + "...")


if __name__ == "__main__":
    test_fixed_prompt_formatting()
