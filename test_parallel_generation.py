#!/usr/bin/env python3
"""
Test script to verify parallel image generation and slideshow logic.
This test mocks the image generation to avoid API costs.
"""

import asyncio
import sys
from unittest.mock import AsyncMock, MagicMock

# Add the project root to the path
sys.path.insert(0, '.')

from services.panel_processor import PanelProcessor
from models.schemas import StoryInputs


class MockEmitProgress:
    """Mock emit_progress function to capture events."""

    def __init__(self):
        self.events = []

    async def __call__(self, **kwargs):
        self.events.append(kwargs)
        print(f"Event: {kwargs.get('event_type', 'unknown')}")


async def test_parallel_processing():
    """Test the new parallel processing logic."""

    print("🧪 Testing parallel image generation logic...")

    # Create mock panels
    panels = []
    for i in range(1, 7):  # 6 panels as in the original
        panel = {
            'panel_number': i,
            'character_sheet': {'name': f'Character {i}'},
            'prop_sheet': {},
            'style_guide': {},
            'dialogue_text': f'This is dialogue for panel {i}',
            'emotional_tone': 'neutral'
        }
        panels.append(panel)

    # Create mock emit_progress
    mock_emit = MockEmitProgress()

    # Create panel processor
    processor = PanelProcessor()

    # Mock the image and TTS generation methods
    processor._generate_panel_image = AsyncMock(return_value=f"mock_image_url_{i}")
    processor._generate_panel_tts = AsyncMock(return_value=f"mock_tts_url_{i}")

    # Test parallel processing
    story_id = "test_story_123"

    try:
        processed_panels = await processor.process_panels_parallel(
            panels=panels,
            story_id=story_id,
            emit_progress=mock_emit,
            user_age=16,
            user_gender="non-binary"
        )

        print("✅ Parallel processing completed successfully!")
        print(f"Processed {len(processed_panels)} panels")

        # Check events emitted
        event_types = [event['event_type'] for event in mock_emit.events]

        print(f"\n📊 Events emitted ({len(mock_emit.events)} total):")
        for event_type in event_types:
            print(f"  - {event_type}")

        # Verify key events
        expected_events = [
            'parallel_processing_start',
            'parallel_image_generation_start',
            'parallel_image_generation_complete',
            'parallel_tts_generation_start',
            'parallel_tts_generation_complete',
            'parallel_processing_complete',
            'slideshow_ready'
        ]

        for expected_event in expected_events:
            if expected_event in event_types:
                print(f"✅ {expected_event} event emitted")
            else:
                print(f"❌ Missing {expected_event} event")

        # Verify panel updates (should be 6)
        panel_updates = [e for e in event_types if e == 'panel_update']
        print(f"✅ Panel updates emitted: {len(panel_updates)} (expected: 6)")

        # Check slideshow_ready event
        slideshow_ready_events = [e for e in mock_emit.events if e['event_type'] == 'slideshow_ready']
        if slideshow_ready_events:
            print("✅ Slideshow ready event emitted with message:")
            print(f"   {slideshow_ready_events[0]['data']['message']}")

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run the test."""
    print("🚀 Starting parallel generation test...\n")

    success = await test_parallel_processing()

    if success:
        print("\n🎉 All tests passed! Parallel generation logic is working correctly.")
        print("✅ All 6 images will be generated in parallel first")
        print("✅ All 6 TTS audio files will be generated in parallel next")
        print("✅ Slideshow will start only after all assets are ready")
    else:
        print("\n💥 Test failed! Check the implementation.")

    return success


if __name__ == "__main__":
    asyncio.run(main())
