"""
Sequential story generation service for reliable panel-by-panel content creation.
This replaces the streaming approach to ensure complete, high-quality content.
"""

import asyncio
import random
from typing import List, Dict, Any, Optional
from loguru import logger
from models.schemas import StoryInputs, StoryGenerationResponse
from services.story_service import story_service
from services.panel_processor import panel_processor
from utils.retry_helpers import exponential_backoff_async
from utils.helpers import create_user_context


class SequentialStoryService:
    """
    Generate story panels in parallel for faster, complete content delivery.
    All panels are generated simultaneously and slideshow starts when all assets are ready.
    """

    def __init__(self):
        self.story_service = story_service

    async def generate_sequential_story(
        self,
        inputs: StoryInputs,
        emit_progress,
        user_age: int = 16,
        user_gender: str = "non-binary",
    ) -> StoryGenerationResponse:
        """
        Generate a complete story using parallel panel processing.

        This method generates all 6 panels simultaneously to ensure
        faster delivery while maintaining high-quality content.
        Slideshow starts only when ALL assets are ready.

        Args:
            inputs: Story generation inputs
            emit_progress: Function to emit progress updates to clients
            user_age: User age for voice selection
            user_gender: User gender for voice selection

        Returns:
            StoryGenerationResponse with all panels and assets
        """
        try:
            story_id = f"story_{asyncio.get_event_loop().time():.0f}"
            # Generate random seed (1-1000) for character consistency across panels
            story_seed = random.randint(1, 1000)
            logger.info(
                f"🚀 Starting sequential story generation for ID: {story_id} (seed: {story_seed})"
            )
            logger.info(
                f"📝 User inputs: nickname={inputs.nickname}, mood={inputs.mood}, age={inputs.age}"
            )

            # Emit story generation start
            await emit_progress(
                event_type="story_generation_start",
                data={"story_id": story_id, "user_inputs": inputs.dict()},
            )

            # Step 1: Generate the basic story structure first
            logger.info("📖 Generating story structure...")
            basic_panels = await self._generate_story_structure(inputs)
            logger.info(f"✅ Story structure generated: {len(basic_panels)} panels")

            # Step 2: Generate detailed content for each panel sequentially
            processed_panels = []

            # Set story context for panel processor (once for all panels)
            # Handle backward compatibility for optional fields
            vibe = getattr(inputs, "vibe", None) or "adventure"
            archetype = getattr(inputs, "archetype", None) or "hero"

            story_context = {
                "mood": inputs.mood,
                "animeGenre": vibe,
                "archetype": archetype,
                "supportSystem": inputs.supportSystem,
                "coreValue": inputs.coreValue,
                "pastResilience": inputs.pastResilience,
                "innerDemon": inputs.innerDemon,
                "desiredOutcome": inputs.desiredOutcome,
                "secretWeapon": inputs.secretWeapon,
                "age": inputs.age,
                "gender": inputs.gender,
            }
            panel_processor.set_story_context(story_context)
            panel_processor.user_age = user_age
            panel_processor.user_gender = user_gender

            # Process ALL panels (1-6) in parallel - no priority for panel 1
            logger.info("🚀 Processing all 6 panels in parallel...")

            async def process_single_panel(panel_index: int, basic_panel: dict):
                panel_number = panel_index + 1
                logger.info(f"📋 Processing panel {panel_number}/6 in parallel...")

                # Emit progress update for this panel
                await emit_progress(
                    event_type="panel_processing_start",
                    data={
                        "panel_number": panel_number,
                        "story_id": story_id,
                        "message": f"Generating panel {panel_number} of 6...",
                    },
                )

                # Generate detailed content for this specific panel
                detailed_panel = await self._generate_panel_content(
                    basic_panel, inputs, panel_number
                )

                # Process panel to generate all assets with timeout and retry
                try:
                    complete_panel = await asyncio.wait_for(
                        panel_processor.process_panel(
                            detailed_panel, story_id, emit_progress, story_seed
                        ),
                        timeout=120.0,  # 2 minute timeout per panel
                    )
                except asyncio.TimeoutError:
                    logger.error(
                        f"Panel {panel_number} processing timed out, using fallback"
                    )
                    # Create fallback panel with basic data
                    complete_panel = {
                        "panel_number": panel_number,
                        "image_url": "",
                        "tts_url": "",
                        "music_url": "/src/assets/audio/background-music.mp3",
                        "dialogue_text": detailed_panel.get(
                            "dialogue_text", self._get_fallback_dialogue(panel_number)
                        ),
                        "emotional_tone": detailed_panel.get(
                            "emotional_tone", "neutral"
                        ),
                        "is_timeout_fallback": True,
                    }

                # Emit panel ready event
                await emit_progress(
                    event_type="panel_ready",
                    data={
                        "panel_number": panel_number,
                        "story_id": story_id,
                        "message": f"Panel {panel_number} is ready!",
                    },
                )

                logger.info(f"✅ Panel {panel_number} completed")
                return complete_panel

            # Create tasks for all 6 panels with optimized concurrency control
            all_panel_tasks = []

            # Import settings for optimization parameters
            from config.settings import settings

            for i, basic_panel in enumerate(basic_panels):
                # Add optimized delay between panel starts
                async def process_with_stagger(panel_index, panel_data):
                    if panel_index > 0:
                        # Use configurable stagger delay (default 0.5s)
                        await asyncio.sleep(
                            panel_index * settings.parallel_panel_stagger_delay
                        )
                    return await process_single_panel(panel_index, panel_data)

                task = process_with_stagger(i, basic_panel)
                all_panel_tasks.append(task)

            # Wait for ALL panels to complete before starting slideshow
            logger.info("⏳ Waiting for all 6 panels to complete...")
            all_panel_results = await asyncio.gather(
                *all_panel_tasks, return_exceptions=True
            )

            # Process results and handle any errors with better fallback
            for i, result in enumerate(all_panel_results):
                if isinstance(result, Exception):
                    logger.error(f"Panel {i+1} failed: {result}")
                    # Create enhanced fallback panel with proper structure
                    fallback_panel = self._create_enhanced_fallback_panel(
                        i + 1, basic_panels[i] if i < len(basic_panels) else None
                    )
                    processed_panels.append(fallback_panel)

                    # Emit fallback panel event
                    await emit_progress(
                        event_type="panel_fallback_used",
                        data={
                            "panel_number": i + 1,
                            "story_id": story_id,
                            "message": f"Using fallback for panel {i + 1}",
                        },
                    )
                else:
                    processed_panels.append(result)

            # Ensure we have exactly 6 panels
            while len(processed_panels) < 6:
                missing_panel_num = len(processed_panels) + 1
                logger.warning(f"Missing panel {missing_panel_num}, creating fallback")
                fallback_panel = self._create_enhanced_fallback_panel(
                    missing_panel_num, None
                )
                processed_panels.append(fallback_panel)

            logger.info("🎉 All 6 panels completed! Preparing slideshow data...")

            # Convert processed panels to frontend-expected format FIRST
            frontend_panels = []
            for i, panel in enumerate(processed_panels):
                frontend_panel = {
                    "id": str(i + 1),
                    "imageUrl": panel.get("image_url", ""),
                    "narrationUrl": panel.get("tts_url", ""),
                    "backgroundMusicUrl": panel.get("music_url", ""),
                    # Include original panel data for debugging
                    "original_data": {
                        "panel_number": panel["panel_number"],
                        "dialogue_text": panel["dialogue_text"],
                        "emotional_tone": panel["emotional_tone"],
                    },
                }
                frontend_panels.append(frontend_panel)

            # NOW emit slideshow start event with ALL panel data included
            await emit_progress(
                event_type="slideshow_start",
                data={
                    "story_id": story_id,
                    "all_panels_ready": True,
                    "total_panels": len(processed_panels),
                    "panels": frontend_panels,  # Include actual panel data
                    "message": "All panels are ready! Starting slideshow...",
                },
            )

            logger.info("🎬 Slideshow start event emitted with all panel data!")

            # Create response data in frontend-expected format
            response_data = {
                "story_id": story_id,
                "panels": frontend_panels,
                "status": "completed",
                "created_at": asyncio.get_event_loop().time(),
                "total_panels": len(processed_panels),
            }

            # Emit story generation completion
            await emit_progress(
                event_type="story_generation_complete",
                data={
                    "story_id": story_id,
                    "story": response_data,
                    "total_panels": len(processed_panels),
                },
            )

            logger.info(f"Sequential story generation completed: {story_id}")

            # Create proper response object
            response = StoryGenerationResponse(
                story_id=story_id,
                status="completed",
                message=f"Manga story '{inputs.mangaTitle}' generated successfully with sequential processing!",
                story=None,  # All data sent via Socket.IO events
            )
            return response

        except Exception as e:
            logger.error(f"Failed to generate sequential story: {e}")

            # Emit error event
            await emit_progress(
                event_type="story_generation_error",
                data={
                    "story_id": story_id if "story_id" in locals() else "",
                    "error": str(e),
                },
            )
            raise

    async def _generate_story_structure(
        self, inputs: StoryInputs
    ) -> List[Dict[str, Any]]:
        """Generate the basic story structure with character sheets and basic content."""
        try:
            logger.info("🤖 Calling story service to generate basic structure...")

            # Add timeout to prevent hanging
            panels = await asyncio.wait_for(
                self.story_service.generate_story_plan(inputs),
                timeout=60.0,  # 60 second timeout for LLM call
            )

            logger.info(f"✅ Generated basic structure for {len(panels)} panels")
            return panels

        except asyncio.TimeoutError:
            logger.error("⏰ Story structure generation timed out, using fallback")
            return self._create_fallback_structure(inputs)
        except Exception as e:
            logger.error(f"❌ Failed to generate story structure: {e}")
            # Return fallback structure
            return self._create_fallback_structure(inputs)

    async def _generate_panel_content(
        self, basic_panel: Dict[str, Any], inputs: StoryInputs, panel_number: int
    ) -> Dict[str, Any]:
        """
        Generate detailed content for a specific panel using targeted AI prompts.
        """
        try:
            logger.info(f"Generating detailed content for panel {panel_number}")

            # Create a focused prompt for this specific panel
            panel_prompt = self._create_panel_specific_prompt(
                basic_panel, inputs, panel_number
            )

            # Generate content with exponential backoff and timeout
            response = await asyncio.wait_for(
                exponential_backoff_async(
                    asyncio.to_thread,
                    self.story_service.llm.invoke,
                    panel_prompt,
                    max_retries=2,  # Reduced retries for faster fallback
                    initial_delay=2.0,
                    max_delay=20.0,
                ),
                timeout=45.0,  # 45 second timeout per panel
            )

            # Extract content from response
            if hasattr(response, "content"):
                response_text = response.content
            else:
                response_text = str(response)

            # Parse the response to extract clean dialogue
            clean_dialogue = self._extract_clean_dialogue(response_text, panel_number)

            # Update the basic panel with detailed content
            detailed_panel = basic_panel.copy()
            detailed_panel.update(
                {
                    "dialogue_text": clean_dialogue,
                    "tts_text": clean_dialogue,  # Same as dialogue for TTS
                }
            )

            logger.info(
                f"Panel {panel_number} detailed content: {clean_dialogue[:50]}..."
            )
            return detailed_panel

        except asyncio.TimeoutError:
            logger.error(
                f"⏰ Panel {panel_number} content generation timed out, using fallback"
            )
            return self._enhance_basic_panel(basic_panel, inputs, panel_number)
        except Exception as e:
            logger.error(
                f"❌ Failed to generate detailed content for panel {panel_number}: {e}"
            )
            # Return basic panel with enhanced fallback
            return self._enhance_basic_panel(basic_panel, inputs, panel_number)

    def _create_panel_specific_prompt(
        self, basic_panel: Dict[str, Any], inputs: StoryInputs, panel_number: int
    ) -> str:
        """Create a focused prompt for generating content for a specific panel."""

        character = basic_panel.get("character_sheet", {})
        emotional_tone = basic_panel.get("emotional_tone", "neutral")

        # Create standardized user context
        user_context = create_user_context(inputs)

        prompt = f"""
You are creating narration content for Panel {panel_number} of a 6-panel manga story.

CHARACTER: {character.get('name', inputs.nickname)} 

USER CONTEXT:
{user_context}

PANEL EMOTIONAL TONE: {emotional_tone}

STORY ARC POSITION:
{self._get_panel_arc_description(panel_number)}

CURRENT PANEL FOCUS: {basic_panel.get('dialogue_text', '')}

Create natural, flowing narration for this panel that:
1. Sounds excellent when read by text-to-speech
2. Is 25-35 words long
3. Captures the emotional tone: {emotional_tone}
4. Continues the character's journey naturally
5. Uses conversational, natural language
6. References their secret weapon ({inputs.secretWeapon}) and desired outcome ({inputs.desiredOutcome}) when appropriate

CRITICAL TTS REQUIREMENTS:
- Do NOT start with "Panel {panel_number}:" or any numbering
- Do NOT use dashes (-), asterisks (*), or formatting symbols
- Do NOT include stage directions like [pause] or (sighs)
- Write as if speaking directly to the listener
- Use proper punctuation for natural speech flow
- Make it sound natural and engaging when spoken

Return ONLY the clean narration text, nothing else:
"""
        return prompt

    def _get_panel_arc_description(self, panel_number: int) -> str:
        """Get the story arc description for a specific panel."""
        arc_map = {
            1: "Introduction - Establish the character and their current state",
            2: "Challenge - Present the obstacle or difficulty they face",
            3: "Reflection - Character processes their situation and feelings",
            4: "Discovery - Character finds inner strength or new perspective",
            5: "Transformation - Character takes positive action or grows",
            6: "Resolution - Character emerges stronger with hope for the future",
        }
        return arc_map.get(panel_number, "Story continues")

    def _extract_clean_dialogue(self, response_text: str, panel_number: int) -> str:
        """Extract clean dialogue from AI response, removing any formatting."""
        try:
            # Remove any panel numbering at the start
            text = response_text.strip()

            # Remove common prefixes
            prefixes_to_remove = [
                f"panel {panel_number}:",
                f"panel_{panel_number}:",
                "dialogue_text:",
                "narration:",
                "-",
                "*",
            ]

            for prefix in prefixes_to_remove:
                if text.lower().startswith(prefix):
                    text = text[len(prefix) :].strip()

            # Remove any quotation marks at start/end
            text = text.strip("\"'")

            # Remove any remaining formatting
            text = (
                text.replace("*", "").replace("-", "").replace("[", "").replace("]", "")
            )

            # Ensure proper sentence structure
            if text and not text[0].isupper():
                text = text[0].upper() + text[1:]

            if text and not text.endswith("."):
                text += "."

            # Validate length and quality
            if len(text.split()) < 10:
                logger.warning(
                    f"Panel {panel_number} dialogue too short, using fallback"
                )
                return self._get_fallback_dialogue(panel_number)

            return text

        except Exception as e:
            logger.error(f"Error extracting dialogue for panel {panel_number}: {e}")
            return self._get_fallback_dialogue(panel_number)

    def _get_fallback_dialogue(self, panel_number: int) -> str:
        """Get high-quality fallback dialogue for a panel."""
        fallbacks = {
            1: "Every journey begins with a single step. Today feels uncertain, but there's something stirring inside, a quiet determination waiting to emerge.",
            2: "The path ahead seems challenging, filled with obstacles that feel overwhelming. Yet deep down, there's a voice whispering that this struggle has meaning.",
            3: "Taking a moment to breathe and reflect on how far the journey has already come. Even in uncertainty, there are small victories worth acknowledging.",
            4: "A spark of clarity emerges. This challenge isn't just about reaching the destination, it's about discovering the strength that was always there.",
            5: "With newfound understanding comes the courage to take action. Each step forward is a choice to believe in the possibility of growth and change.",
            6: "Looking back on this journey, it's clear how much has changed. The path continues ahead, but now it's illuminated by hope and self-belief.",
        }
        return fallbacks.get(
            panel_number, "The journey continues with hope and determination."
        )

    def _enhance_basic_panel(
        self, basic_panel: Dict[str, Any], inputs: StoryInputs, panel_number: int
    ) -> Dict[str, Any]:
        """Enhance a basic panel with better fallback content."""
        enhanced_dialogue = self._get_fallback_dialogue(panel_number)

        enhanced_panel = basic_panel.copy()
        enhanced_panel.update(
            {
                "dialogue_text": enhanced_dialogue,
                "tts_text": enhanced_dialogue,
            }
        )

        return enhanced_panel

    def _create_fallback_structure(self, inputs: StoryInputs) -> List[Dict[str, Any]]:
        """Create fallback structure when AI generation fails."""
        panels = []

        for i in range(1, 7):
            panel = {
                "panel_number": i,
                "character_sheet": {
                    "name": inputs.nickname,
                    "age": str(inputs.age),
                    "appearance": f"determined {inputs.gender} with expressive eyes",
                    "personality": "hopeful and resilient",
                    "goals": getattr(inputs, "dream", None) or inputs.desiredOutcome,
                    "fears": f"struggles with {inputs.innerDemon}",
                    "strengths": inputs.secretWeapon,
                },
                "prop_sheet": {
                    "items": [getattr(inputs, "hobby", None) or inputs.secretWeapon],
                    "environment": f"{getattr(inputs, 'vibe', None) or 'adventure'} setting that supports {inputs.coreValue}",
                    "lighting": "warm and hopeful",
                    "mood_elements": [inputs.coreValue, "growth", "hope"],
                },
                "style_guide": {
                    "art_style": "modern manga style",
                    "visual_elements": ["emotional expression", "dynamic composition"],
                    "framing": "cinematic panel layout",
                },
                "dialogue_text": self._get_fallback_dialogue(i),
                "emotional_tone": [
                    "neutral",
                    "tense",
                    "contemplative",
                    "hopeful",
                    "determined",
                    "uplifting",
                ][i - 1],
                "image_prompt": "",
                "music_prompt": "",
                "tts_text": self._get_fallback_dialogue(i),
            }
            panels.append(panel)

        return panels

    def _create_fallback_panel(self, panel_number: int) -> Dict[str, Any]:
        """Create a fallback panel when processing fails."""
        return {
            "panel_number": panel_number,
            "image_url": "",
            "tts_url": "",
            "music_url": "/src/assets/audio/background-music.mp3",
            "dialogue_text": self._get_fallback_dialogue(panel_number),
            "emotional_tone": "neutral",
        }

    def _create_enhanced_fallback_panel(
        self, panel_number: int, basic_panel: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Create an enhanced fallback panel with better content."""
        # Use basic panel data if available, otherwise create from scratch
        if basic_panel:
            dialogue = basic_panel.get(
                "dialogue_text", self._get_fallback_dialogue(panel_number)
            )
            emotional_tone = basic_panel.get("emotional_tone", "neutral")
        else:
            dialogue = self._get_fallback_dialogue(panel_number)
            emotional_tone = (
                [
                    "neutral",
                    "tense",
                    "contemplative",
                    "hopeful",
                    "determined",
                    "uplifting",
                ][panel_number - 1]
                if panel_number <= 6
                else "neutral"
            )

        return {
            "panel_number": panel_number,
            "image_url": "",  # Will be handled by frontend fallback
            "tts_url": "",  # Will be handled by frontend fallback
            "music_url": "/src/assets/audio/background-music.mp3",
            "dialogue_text": dialogue,
            "emotional_tone": emotional_tone,
            "is_fallback": True,  # Flag for frontend to handle differently
        }


# Global sequential story service instance
sequential_story_service = SequentialStoryService()
