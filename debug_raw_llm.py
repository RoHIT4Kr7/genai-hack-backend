#!/usr/bin/env python3
"""
Simple test to check the raw LLM response for Story Architect.
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.helpers import STORY_ARCHITECT_PROMPT, create_user_context
from models.schemas import StoryInputs
import google.generativeai as genai
from config.settings import settings
import asyncio


async def test_raw_llm_response():
    """Test the raw LLM response to see dialogue generation."""

    # Configure Gemini
    genai.configure(api_key=settings.gemini_api_key)
    model = genai.GenerativeModel("gemini-2.0-flash-exp")

    # Create test input
    test_inputs = StoryInputs(
        name="tanishq",
        nickname="tanishq",
        age="19",
        gender="male",
        archetype="hero",
        mood="happy",
        dream="I want to become a great software engineer",
        hobby="coding",
        struggle="I doubt my coding abilities",
        secretWeapon="I never give up",
        coreValue="helping others",
        supportSystem="family",
        vibe="motivational",
        desiredOutcome="building confidence",
    )

    print("🔍 Testing raw Story Architect LLM response...")
    print(f"Input: {test_inputs.nickname}, {test_inputs.age}, {test_inputs.gender}")
    print("-" * 80)

    try:
        # Generate the prompt
        user_context = create_user_context(test_inputs)
        prompt = STORY_ARCHITECT_PROMPT.format(user_context=user_context)

        print("📝 Generated prompt snippet:")
        print(prompt[:500] + "...")
        print("-" * 80)

        print("🤖 Calling Gemini 2.0 Flash...")

        # Call the LLM
        response = model.generate_content(prompt)

        print("📄 Raw LLM Response:")
        print("-" * 80)
        print(response.text[:2000])  # First 2000 chars
        print("-" * 80)

        # Look for panel dialogue patterns
        import re

        for i in range(1, 7):
            patterns = [
                rf'PANEL_{i}:\s*dialogue_text:\s*"([^"]*)"',
                rf"PANEL_{i}:\s*dialogue_text:\s*([^\n]+)",
            ]

            for pattern in patterns:
                match = re.search(pattern, response.text, re.DOTALL | re.IGNORECASE)
                if match:
                    dialogue = match.group(1).strip()
                    word_count = len(dialogue.split())
                    print(f"Panel {i}: '{dialogue}' ({word_count} words)")

                    if word_count < 10:
                        print(f"  ⚠️  WARNING: Too short! Expected ~25-35 words")
                    break
            else:
                print(f"Panel {i}: ❌ No dialogue found")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_raw_llm_response())
