"""
Test to verify if the STORY_ARCHITECT_PROMPT is properly formatted with user context
"""

from models.schemas import StoryInputs
from utils.helpers import STORY_ARCHITECT_PROMPT


def test_prompt_formatting():
    """Test how the prompt is being constructed"""

    print("🔍 TESTING PROMPT CONSTRUCTION")
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

    # Recreate the same prompt construction as streaming_parser.py
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

    print("\n🎨 STORY ARCHITECT PROMPT (first 500 chars):")
    print(STORY_ARCHITECT_PROMPT[:500] + "...")

    print("\n🔗 CHECKING FOR user_context PLACEHOLDER:")
    if "{user_context}" in STORY_ARCHITECT_PROMPT:
        print("❌ FOUND: {user_context} placeholder exists but is NOT being filled!")
        print(
            "This means the CHARACTER_SHEET section is not getting the actual user data!"
        )
    else:
        print("✅ No {user_context} placeholder found")

    # Show how the prompt is ACTUALLY being combined (from streaming_parser.py)
    full_prompt = STORY_ARCHITECT_PROMPT + "\n\n" + input_context

    print("\n⚡ ACTUAL PROMPT CONSTRUCTION:")
    print("Method: STORY_ARCHITECT_PROMPT + input_context (simple concatenation)")
    print(f"Total length: {len(full_prompt)} characters")

    # Check if the CHARACTER_SHEET instructions mention the gender
    character_sheet_section = STORY_ARCHITECT_PROMPT[
        STORY_ARCHITECT_PROMPT.find("CHARACTER_SHEET") : STORY_ARCHITECT_PROMPT.find(
            "PROP_SHEET"
        )
    ]
    print("\n🎭 CHARACTER_SHEET GENDER INSTRUCTIONS:")
    if "EXACT_USER_GENDER_IDENTITY_MANDATORY_NO_CHANGES" in character_sheet_section:
        print("✅ Found ultra-aggressive gender enforcement in CHARACTER_SHEET")
    else:
        print("❌ No gender enforcement found")

    # Check if the user's actual gender appears in the final prompt
    if f"Gender: {test_inputs.gender}" in full_prompt:
        print(f"✅ User's actual gender '{test_inputs.gender}' appears in final prompt")
    else:
        print(f"❌ User's gender '{test_inputs.gender}' NOT found in final prompt")


if __name__ == "__main__":
    test_prompt_formatting()
