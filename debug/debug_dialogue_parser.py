#!/usr/bin/env python3
"""
Quick debug script to validate dialogue extraction paths without calling external APIs.
"""

import sys
import os
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.story_service import story_service
from models.schemas import StoryInputs

# Simulated LLM response loosely following STORY_ARCHITECT_PROMPT output
SIMULATED_RESPONSE = """
CHARACTER_SHEET:
{
  "name": "Tanishq",
  "age": "young-adult",
  "gender": "male",
  "appearance": "oval face, brown eyes, short black hair, average height, casual hoodie",
  "personality": "determined yet thoughtful",
  "goals": "become a great software engineer",
  "fears": "self-doubt and uncertainty",
  "strengths": "never give up attitude"
}

PROP_SHEET:
{
  "items": ["laptop with stickers", "notebook with sketches"],
  "environment": "motivational workspace with warm lighting",
  "lighting": "golden hour ambient light",
  "mood_elements": ["hope", "growth", "focus"]
}

STYLE_GUIDE:
{
  "art_style": "Studio Ghibli inspired soft watercolor environments",
  "visual_elements": ["soft natural lighting", "organic textures", "warm colors"]
}

PANEL_1:
dialogue_text: "Today I'm feeling happy, but there's a quiet pressure under the surface. I want to grow into the engineer I imagine, one step at a time, with patience and focus."

PANEL_2:
dialogue_text: "Sometimes I doubt my skills when things get hard. But even in those moments, I try to breathe, reflect, and remember how far I've already come."

PANEL_3:
dialogue_text: "I pause to look at my notes and patterns that worked before. I realize I don't have to be perfect today; I only need to keep learning and showing up."

PANEL_4:
dialogue_text: "I remember my secret weapon— I never give up on learning. I ask for help when stuck, and with each answer, my confidence gets a little stronger."

PANEL_5:
dialogue_text: "I open my IDE and start building again. Small successes stack up into momentum. I use my curiosity to explore and my patience to debug with calm."

PANEL_6:
dialogue_text: "I feel hopeful about tomorrow. Challenges won't disappear, but my mindset is steadier now. I'm building both skills and trust in myself—with gratitude for everyone helping me grow."
"""


def main():
    inputs = StoryInputs(
        mood="happy",
        coreValue="helping others through technology",
        supportSystem="family and coding community",
        pastResilience="kept practicing through hard problems",
        innerDemon="self-doubt",
        desiredOutcome="build confidence in my abilities",
        nickname="Tanishq",
        secretWeapon="never give up when learning",
        age="young-adult",
        gender="male",
        vibe="motivational",
        dream="become a great software engineer",
        hobby="coding and building projects",
    )

    panels = story_service._parse_story_architect_response(SIMULATED_RESPONSE, inputs)
    print(f"Parsed {len(panels)} panels\n")
    for p in panels:
        print(f"Panel {p['panel_number']}: {p['dialogue_text'][:80]}...\n")


if __name__ == "__main__":
    main()
