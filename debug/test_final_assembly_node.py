#!/usr/bin/env python3
import os
import sys
import asyncio

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from workflows.manga_workflow import final_assembly_node
from models.schemas import StoryInputs


async def main():
    inputs = StoryInputs(
        mood="happy",
        coreValue="kindness",
        supportSystem="family",
        pastResilience="kept going",
        innerDemon="self-doubt",
        desiredOutcome="confidence",
        nickname="Alex",
        secretWeapon="curiosity",
        age="young-adult",
        gender="male",
        vibe="motivational",
    )

    # Panels with empty prop/style to simulate missing data
    panels = [
        {
            "panel_number": i,
            "character_sheet": {},
            "prop_sheet": {},
            "style_guide": {},
            "dialogue_text": f"Panel {i} dialogue text that is definitely long enough to pass checks.",
            "emotional_tone": "neutral",
            "tts_text": f"Panel {i} tts",
        }
        for i in range(1, 7)
    ]

    state = {
        "story_id": "story_test_final_assembly",
        "inputs": inputs,
        "panels": panels,
        "image_urls": [f"https://example.com/p{i}.png" for i in range(1, 7)],
        "background_urls": [f"https://example.com/b{i}.mp3" for i in range(1, 7)],
        "tts_urls": [f"https://example.com/t{i}.mp3" for i in range(1, 7)],
        "status": "pending",
    }

    new_state = await final_assembly_node(state)
    print("status=", new_state.get("status"))
    if new_state.get("status") == "completed":
        print("Enriched panels:")
        for p in new_state["panels"]:
            # Ensure nested fields are present
            assert p.prop_sheet.items
            assert p.style_guide.art_style
            print(p.panel_number, p.image_url, p.tts_url, p.music_url)
    else:
        print("error=", new_state.get("error"))


if __name__ == "__main__":
    asyncio.run(main())
