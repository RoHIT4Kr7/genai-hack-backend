#!/usr/bin/env python3
"""
Quick test to debug the Story Architect dialogue generation issue.
This will help us see exactly what the LLM is generating.
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.streaming_parser import StreamingStoryGenerator
from models.schemas import StoryInputs
import asyncio
import json


async def test_story_generation():
    """Test the story generation with a simple input to debug dialogue fragmentation."""

    # Create a simple test input
    test_inputs = StoryInputs(
        name="tanishq",
        nickname="tanishq",
        age="19",
        gender="male",
        archetype="hero",
        mood="happy",
        dream="I want to become a great software engineer and build apps that help people",
        hobby="I love coding and building small projects",
        struggle="I often doubt my abilities when learning new technologies",
        secretWeapon="I never give up and always keep learning from mistakes",
        coreValue="helping others through technology",
        supportSystem="family and friends",
        vibe="motivational",
        desiredOutcome="building confidence in my coding abilities",
    )

    # Create parser and generate story
    parser = StreamingStoryGenerator()

    print("🔍 Testing Story Architect generation...")
    print(f"Input: {test_inputs.name}, {test_inputs.age}, {test_inputs.gender}")
    print("-" * 60)

    try:
        panels = await parser.generate_streaming_story(test_inputs)

        print(f"✅ Generated {len(panels)} panels")
        print("-" * 60)

        for i, panel in enumerate(panels, 1):
            dialogue = panel.get("dialogue_text", "No dialogue")
            print(f"Panel {i}:")
            print(f"  Dialogue: '{dialogue}'")
            print(f"  Length: {len(dialogue)} characters")
            print(f"  Emotional tone: {panel.get('emotional_tone', 'N/A')}")
            print()

            # Check if dialogue is suspiciously short
            if len(dialogue) < 15:
                print(f"⚠️  WARNING: Panel {i} dialogue is too short!")
                print(
                    f"     Expected: 25-35 words, Got: ~{len(dialogue.split())} words"
                )
                print()

    except Exception as e:
        print(f"❌ Error during generation: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_story_generation())
