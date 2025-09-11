import asyncio
import json
import re
from typing import List, Dict, Any, Optional
from langchain_google_vertexai import ChatVertexAI
from langchain.prompts import PromptTemplate
from loguru import logger
from config.settings import settings
from models.schemas import (
    StoryInputs,
    GeneratedStory,
    PanelData,
    StoryGenerationResponse,
)
from utils.helpers import (
    STORY_ARCHITECT_PROMPT,
    VISUAL_ARTIST_PROMPT,
    validate_story_consistency,
    create_structured_image_prompt,
    generate_panel_prompt,
    get_manga_style_by_mood,
    create_user_context,
)
from utils.retry_helpers import exponential_backoff_async
from services.image_service import image_service
from services.audio_service import audio_service
from services.storage_service import storage_service
from services.streaming_parser import StreamingStoryGenerator
from services.panel_processor import panel_processor


class StoryService:
    def __init__(self):
        self.llm = None
        self.streaming_generator = None
        self._initialize_llm()
        self._initialize_streaming_generator()

    def _initialize_llm(self):
        """Initialize ChatVertexAI LLM with hardcoded configuration."""
        try:
            # Hardcoded configuration - SDK uses GOOGLE_APPLICATION_CREDENTIALS automatically
            self.llm = ChatVertexAI(
                model_name=settings.model_name,
                project=settings.vertex_ai_project_id,
                temperature=0.9,
                max_output_tokens=8192,
            )
            logger.info("Story service ChatVertexAI initialized")

        except Exception as e:
            logger.error(f"Failed to initialize story service LLM: {e}")
            raise

    def _initialize_streaming_generator(self):
        """Initialize the streaming story generator."""
        try:
            self.streaming_generator = StreamingStoryGenerator(self)
            logger.info("Streaming story generator initialized")

        except Exception as e:
            logger.error(f"Failed to initialize streaming generator: {e}")
            # Don't raise here - allow service to work without streaming

    async def generate_story_plan(self, inputs: StoryInputs) -> List[Dict[str, Any]]:
        """Generate the complete 6-panel story plan using three specialized AI roles."""
        try:
            # Fallback if LLM is not initialized (hackathon-safe default)
            if self.llm is None:
                logger.warning("🚨 LLM not initialized; using fallback story plan")
                return self._create_fallback_panels()

            logger.info("🎭 Starting story generation with 3 specialized AI roles")
            logger.info(
                f"📝 Input validation: nickname='{inputs.nickname}', mood='{inputs.mood}'"
            )

            # Step 1: Generate story structure with Story Architect AI
            logger.info(
                "🏗️ Step 1: Generating story structure with Story Architect AI..."
            )
            panels = await self._generate_story_structure(inputs)
            logger.info(f"✅ Step 1 complete: Generated {len(panels)} panels")

            # Step 2: Generate image prompts with Visual Artist AI (parallel)
            image_prompts = await self._generate_image_prompts(panels)

            # Step 3: Combine all content into final panels (using static background music)
            final_panels = self._combine_ai_responses(panels, image_prompts)

            # Validate consistency
            if not validate_story_consistency(final_panels):
                logger.warning("Story consistency validation failed, regenerating...")
                return await self.generate_story_plan(inputs)

            logger.info("Story plan generated successfully with all AI roles")
            return final_panels

        except Exception as e:
            logger.error(f"Failed to generate story plan: {e}")
            raise

    async def _generate_story_structure(
        self, inputs: StoryInputs
    ) -> List[Dict[str, Any]]:
        """Step 1: Generate story structure using Story Architect AI."""
        try:
            # Create standardized user context
            logger.info("📋 Creating user context...")
            user_context = create_user_context(inputs)
            logger.info(f"✅ User context created: {len(user_context)} characters")

            # Combine Story Architect prompt with user context
            logger.info("🎨 Combining Story Architect prompt with user context...")
            full_prompt = STORY_ARCHITECT_PROMPT.format(user_context=user_context)
            logger.info(f"✅ Full prompt created: {len(full_prompt)} characters")

            logger.info("🤖 Calling LLM with Story Architect prompt...")

            # Generate the story structure with exponential backoff
            response = await exponential_backoff_async(
                asyncio.to_thread,
                self.llm.invoke,
                full_prompt,
                max_retries=3,
                initial_delay=2.0,
                max_delay=30.0,
            )

            # Extract content from ChatVertexAI response
            if hasattr(response, "content"):
                response_text = response.content
            else:
                response_text = str(response)

            # Parse the Story Architect response
            panels = self._parse_story_architect_response(response_text, inputs)

            logger.info("Story structure generated successfully")
            return panels

        except Exception as e:
            logger.error(f"Failed to generate story structure: {e}")
            raise

    async def _generate_image_prompts(self, panels: List[Dict[str, Any]]) -> List[str]:
        """Step 2: Generate image prompts using Visual Artist AI."""
        try:
            logger.info("Generating image prompts with Visual Artist AI")

            async def generate_single_image_prompt(
                panel_data: Dict[str, Any], panel_num: int
            ) -> str:
                try:
                    # Use the new generate_panel_prompt function for consistent, panel-specific prompts
                    image_prompt = generate_panel_prompt(panel_num, panel_data)

                    # For compatibility with existing Visual Artist AI, still create the structured input
                    visual_input = f"""
                    CHARACTER_SHEET:
                    {json.dumps(panel_data['character_sheet'], indent=2)}

                    PROP_SHEET:
                    {json.dumps(panel_data['prop_sheet'], indent=2)}

                    STYLE_GUIDE:
                    {json.dumps(panel_data['style_guide'], indent=2)}

                    dialogue_text: "{panel_data['dialogue_text']}"

                    GENERATED IMAGE PROMPT:
                    {image_prompt}

                    Please refine and enhance the above image generation prompt for Panel {panel_num}.
                    """

                    # Combine Visual Artist prompt with panel data
                    full_prompt = VISUAL_ARTIST_PROMPT + "\n\n" + visual_input

                    # Generate image prompt with exponential backoff
                    response = await exponential_backoff_async(
                        asyncio.to_thread,
                        self.llm.invoke,
                        full_prompt,
                        max_retries=3,
                        initial_delay=2.0,
                        max_delay=30.0,
                    )

                    # Extract content
                    if hasattr(response, "content"):
                        response_text = response.content
                    else:
                        response_text = str(response)

                    return response_text.strip()

                except Exception as e:
                    logger.error(
                        f"Failed to generate image prompt for panel {panel_num}: {e}"
                    )
                    return f"Manga panel {panel_num} illustration"

            # Generate all image prompts in parallel
            tasks = [
                generate_single_image_prompt(panel, i)
                for i, panel in enumerate(panels, 1)
            ]
            image_prompts = await asyncio.gather(*tasks)

            logger.info("Image prompts generated successfully")
            return image_prompts

        except Exception as e:
            logger.error(f"Failed to generate image prompts: {e}")
            # Return fallback prompts
            return [f"Manga panel {i} illustration" for i in range(1, 7)]

    def _parse_story_architect_response(
        self, response: str, inputs: StoryInputs = None
    ) -> List[Dict[str, Any]]:
        """Parse the Story Architect AI response into structured panel data."""
        try:
            panels = []

            # Extract character sheet
            character_match = re.search(
                r"CHARACTER_SHEET:\s*({.*?})", response, re.DOTALL
            )
            character_sheet = (
                json.loads(character_match.group(1)) if character_match else {}
            )

            # Extract prop sheet
            prop_match = re.search(r"PROP_SHEET:\s*({.*?})", response, re.DOTALL)
            prop_sheet = json.loads(prop_match.group(1)) if prop_match else {}

            # Extract style guide
            style_match = re.search(r"STYLE_GUIDE:\s*({.*?})", response, re.DOTALL)
            style_guide = json.loads(style_match.group(1)) if style_match else {}

            # Extract each panel dialogue text
            for i in range(1, 7):
                panel_pattern = rf'PANEL_{i}:\s*dialogue_text:\s*"([^"]*)"'
                panel_match = re.search(panel_pattern, response, re.DOTALL)

                if panel_match:
                    panel_data = {
                        "panel_number": i,
                        "character_sheet": character_sheet,
                        "prop_sheet": prop_sheet,
                        "style_guide": style_guide,
                        "dialogue_text": panel_match.group(1),
                        "emotional_tone": self._determine_emotional_tone(
                            i, panel_match.group(1)
                        ),
                    }
                    panels.append(panel_data)
                else:
                    # Fallback if parsing fails
                    panel_data = {
                        "panel_number": i,
                        "character_sheet": character_sheet,
                        "prop_sheet": prop_sheet,
                        "style_guide": style_guide,
                        "dialogue_text": f"Panel {i} dialogue",
                        "emotional_tone": "neutral",
                    }
                    panels.append(panel_data)

            return panels

        except Exception as e:
            logger.error(f"Failed to parse Story Architect response: {e}")
            # Return fallback panels with user context
            return self._create_fallback_panels(inputs)

    def _combine_ai_responses(
        self, panels: List[Dict[str, Any]], image_prompts: List[str]
    ) -> List[Dict[str, Any]]:
        """Combine responses from Story Architect and Visual Artist AI into final panels."""
        try:
            combined_panels = []

            for i, panel in enumerate(panels):
                combined_panel = panel.copy()

                # Add image prompt from Visual Artist AI
                if i < len(image_prompts):
                    combined_panel["image_prompt"] = image_prompts[i]
                else:
                    combined_panel["image_prompt"] = f"Manga panel {i+1} illustration"

                # Use static background music and dialogue text for TTS
                combined_panel["music_url"] = "/src/assets/audio/background-music.mp3"
                combined_panel["tts_text"] = panel["dialogue_text"]

                combined_panels.append(combined_panel)

            logger.info("Successfully combined AI responses from all three roles")
            return combined_panels

        except Exception as e:
            logger.error(f"Failed to combine AI responses: {e}")
            return panels  # Return original panels if combination fails

    def _parse_story_response(
        self, response: str, inputs: StoryInputs = None
    ) -> List[Dict[str, Any]]:
        """Parse the LLM response into structured panel data."""
        try:
            panels = []

            # Extract character sheet
            character_match = re.search(
                r"CHARACTER_SHEET:\s*({.*?})", response, re.DOTALL
            )
            character_sheet = (
                json.loads(character_match.group(1)) if character_match else {}
            )

            # Extract prop sheet
            prop_match = re.search(r"PROP_SHEET:\s*({.*?})", response, re.DOTALL)
            prop_sheet = json.loads(prop_match.group(1)) if prop_match else {}

            # Extract style guide
            style_match = re.search(r"STYLE_GUIDE:\s*({.*?})", response, re.DOTALL)
            style_guide = json.loads(style_match.group(1)) if style_match else {}

            # Extract each panel
            for i in range(1, 7):
                panel_pattern = rf'PANEL_{i}:\s*dialogue_text:\s*"([^"]*)"\s*image_prompt:\s*"([^"]*)"\s*music_prompt:\s*"([^"]*)"'
                panel_match = re.search(panel_pattern, response, re.DOTALL)

                if panel_match:
                    panel_data = {
                        "panel_number": i,
                        "character_sheet": character_sheet,
                        "prop_sheet": prop_sheet,
                        "style_guide": style_guide,
                        "dialogue_text": panel_match.group(1),
                        "image_prompt": panel_match.group(2),
                        "music_prompt": panel_match.group(3),
                        "emotional_tone": self._determine_emotional_tone(
                            i, panel_match.group(1)
                        ),
                    }
                    panels.append(panel_data)
                else:
                    # Fallback if parsing fails
                    panel_data = {
                        "panel_number": i,
                        "character_sheet": character_sheet,
                        "prop_sheet": prop_sheet,
                        "style_guide": style_guide,
                        "dialogue_text": f"Panel {i} dialogue",
                        "image_prompt": f"Manga panel {i} illustration",
                        "music_prompt": f"Emotional music for panel {i}",
                        "emotional_tone": "neutral",
                    }
                    panels.append(panel_data)

            return panels

        except Exception as e:
            logger.error(f"Failed to parse story response: {e}")
            # Return fallback panels with user context
            return self._create_fallback_panels(inputs)

    def _determine_emotional_tone(self, panel_number: int, dialogue: str) -> str:
        """Determine emotional tone based on panel number and dialogue."""
        emotional_arc = {
            1: "neutral",  # Introduction
            2: "tense",  # Challenge
            3: "contemplative",  # Reflection
            4: "hopeful",  # Discovery
            5: "determined",  # Transformation
            6: "uplifting",  # Resolution
        }
        return emotional_arc.get(panel_number, "neutral")

    def _create_fallback_panels(
        self, inputs: StoryInputs = None
    ) -> List[Dict[str, Any]]:
        """Create fallback panels with manga style mapping."""
        panels = []

        # Get manga style based on user mood/vibe (with backward compatibility)
        manga_style = "classic shonen manga style"
        if inputs:
            vibe_value = (
                self._get_legacy_field_value(inputs, "vibe", "vibe") or "shonen"
            )
            manga_style = get_manga_style_by_mood(inputs.mood, vibe_value)

        for i in range(1, 7):
            # Extract field values to avoid f-string backslash issues
            secret_weapon = (
                self._get_legacy_field_value(inputs, "secretWeapon", "hobby")
                or "creative"
            )
            inner_demon = (
                self._get_legacy_field_value(inputs, "innerDemon", "mood")
                or "uncertainty"
            )
            support_system = (
                self._get_legacy_field_value(inputs, "supportSystem", "vibe")
                or "inspiring"
            )
            core_value = (
                self._get_legacy_field_value(inputs, "coreValue", "vibe") or "hope"
            )

            panel_data = {
                "panel_number": i,
                "character_sheet": {
                    "name": inputs.nickname if inputs else "Hero",
                    "age": inputs.age if inputs else "young-adult",
                    "appearance": f"determined {inputs.gender if inputs else 'person'} with expressive eyes and {secret_weapon} aesthetic",
                    "clothing": "modern casual outfit that reflects their personality",
                    "personality": "determined and hopeful",
                    "goals": self._get_legacy_field_value(
                        inputs, "desiredOutcome", "dream"
                    )
                    or "overcome challenges",
                    "fears": f"struggles with {inner_demon}",
                    "strengths": f"inner resilience, {secret_weapon}",
                },
                "prop_sheet": {
                    "items": [secret_weapon, "meaningful object"],
                    "environment": f"{support_system} setting that supports growth",
                    "lighting": "dynamic lighting that conveys emotional state",
                    "mood_elements": [core_value, "growth", "determination"],
                },
                "style_guide": {
                    "art_style": manga_style,
                    "visual_elements": [
                        "dynamic composition",
                        "emotional expression",
                        "typography dialogue",
                    ],
                    "framing": "cinematic manga panel composition",
                    "details": "strong ink lines, detailed cross-hatching, high contrast",
                },
                "dialogue_text": f"Panel {i}: The journey of {inputs.nickname if inputs else 'our hero'} continues with {secret_weapon}...",
                "image_prompt": f"Manga panel showing character's emotional journey in {manga_style}",
                "music_prompt": f"Emotional {core_value} music for panel {i}",
                "emotional_tone": self._determine_emotional_tone(i, ""),
            }
            panels.append(panel_data)
        return panels

    def _convert_age_range_to_int(self, age_range: str) -> int:
        """Convert age range string to approximate integer for voice selection."""
        age_mapping = {
            "teen": 16,
            "young-adult": 22,
            "adult": 30,
            "mature": 45,
            "senior": 65,
            "not-specified": 25,  # Default middle age
        }
        return age_mapping.get(age_range, 25)  # Default to 25 if unknown range

    def _get_legacy_field_value(
        self, inputs: StoryInputs, new_field: str, legacy_field: str
    ) -> str:
        """Get field value with backward compatibility for legacy field names."""
        if hasattr(inputs, new_field) and getattr(inputs, new_field):
            return getattr(inputs, new_field)
        elif hasattr(inputs, legacy_field) and getattr(inputs, legacy_field):
            return getattr(inputs, legacy_field)
        return ""

    async def generate_complete_story(self, inputs: StoryInputs) -> GeneratedStory:
        """Generate a complete story with images and audio."""
        try:
            story_id = f"story_{asyncio.get_event_loop().time():.0f}"
            logger.info(f"Starting story generation for ID: {story_id}")

            # Step 1: Generate story plan
            panels = await self.generate_story_plan(inputs)

            # Step 2: Generate images (async)
            image_task = asyncio.create_task(
                image_service.generate_panel_images(panels, story_id)
            )

            # Step 3: Generate audio with personalized voices (async)
            # Convert age range string to approximate int for voice selection
            user_age = self._convert_age_range_to_int(inputs.age)
            audio_task = asyncio.create_task(
                audio_service.generate_all_audio(
                    panels, story_id, user_age, inputs.gender
                )
            )

            # Wait for both tasks to complete
            image_urls, (background_urls, tts_urls) = await asyncio.gather(
                image_task, audio_task
            )

            # Step 4: Create final story object (no audio synchronization)
            story = GeneratedStory(
                story_id=story_id,
                panels=panels,
                image_urls=image_urls,
                audio_url="",  # No synchronized audio - separate background and TTS URLs available
                status="completed",
            )

            logger.info(f"Story generation completed: {story_id}")
            return story

        except Exception as e:
            logger.error(f"Failed to generate complete story: {e}")
            raise

    async def generate_streaming_story(
        self,
        inputs: StoryInputs,
        emit_progress,
        user_age: int = 16,
        user_gender: str = "non-binary",
    ) -> GeneratedStory:
        """
        Generate a complete story using streaming panel-by-panel processing.

        This method streams the story generation process and immediately processes
        each panel as it becomes available, providing real-time progress updates.

        Args:
            inputs: Story generation inputs
            emit_progress: Function to emit progress updates to clients
            user_age: User age for voice selection
            user_gender: User gender for voice selection

        Returns:
            GeneratedStory with all panels and assets
        """
        try:
            story_id = f"story_{asyncio.get_event_loop().time():.0f}"
            logger.info(f"Starting streaming story generation for ID: {story_id}")

            # Emit story generation start
            await emit_progress(
                event_type="story_generation_start",
                data={"story_id": story_id, "user_inputs": inputs.dict()},
            )

            # Check if streaming generator is available
            if self.streaming_generator is None:
                logger.warning(
                    "Streaming generator not available, falling back to regular generation"
                )
                return await self.generate_complete_story(inputs)

            # Generate panels using streaming parser
            panels_stream = self.streaming_generator.generate_streaming_story(
                inputs, emit_progress
            )

            # Set story context for dynamic music prompts with backward compatibility
            story_context = {
                "mood": inputs.mood,
                "animeGenre": self._get_legacy_field_value(inputs, "vibe", "vibe")
                or "adventure",  # Map vibe to animeGenre for compatibility
                "archetype": self._get_legacy_field_value(
                    inputs, "archetype", "archetype"
                )
                or "hero",
                "supportSystem": inputs.supportSystem,
                "coreValue": inputs.coreValue,
                "pastResilience": inputs.pastResilience,  # Use new field directly
                "innerDemon": inputs.innerDemon,
                "desiredOutcome": inputs.desiredOutcome,
                "secretWeapon": inputs.secretWeapon,
                "age": inputs.age,
                "gender": inputs.gender,
            }
            panel_processor.set_story_context(story_context)

            # Collect all panels first, then process in parallel
            all_panels = []
            async for panel_data in panels_stream:
                all_panels.append(panel_data)

            logger.info(f"Collected {len(all_panels)} panels for parallel processing")

            # Convert age range to int for voice selection
            user_age_int = self._convert_age_range_to_int(inputs.age)

            # Process all panels in parallel (generate all images first, then all audio)
            processed_panels = await panel_processor.process_panels_parallel(
                all_panels,
                story_id,
                emit_progress,
                user_age_int,
                inputs.gender,
                story_seed=None,
            )

            # Convert processed panels to frontend-expected format
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

            # Create response data in frontend-expected format
            response_data = {
                "story_id": story_id,
                "panels": frontend_panels,
                "status": "completed",
                "created_at": asyncio.get_event_loop().time(),
                "total_panels": len(processed_panels),
            }

            # Emit story generation completion with frontend-compatible data
            await emit_progress(
                event_type="story_generation_complete",
                data={
                    "story_id": story_id,
                    "story": response_data,
                    "total_panels": len(processed_panels),
                    "slideshow_ready": True,  # All assets are generated and ready
                    "message": "Story generation completed. All 6 images and audio assets are ready for slideshow.",
                },
            )

            logger.info(f"Streaming story generation completed: {story_id}")

            # Create proper response object without datetime objects
            response = StoryGenerationResponse(
                story_id=story_id,
                status="completed",
                message=f"Manga story '{inputs.mangaTitle}' generated successfully with streaming!",
                story=None,  # All data sent via Socket.IO events
            )
            return response

        except Exception as e:
            logger.error(f"Failed to generate streaming story: {e}")

            # Emit error event
            await emit_progress(
                event_type="story_generation_error",
                data={
                    "story_id": story_id if "story_id" in locals() else "",
                    "error": str(e),
                },
            )
            raise

    async def get_story_status(self, story_id: str) -> Dict[str, Any]:
        """Get the status of a story generation."""
        try:
            # Check if assets exist in storage
            assets = await storage_service.get_story_assets(story_id)

            status = {
                "story_id": story_id,
                "status": (
                    "completed" if len(assets) >= 13 else "in_progress"
                ),  # 6 images + 6 music + 6 tts + 1 final audio
                "assets_count": len(assets),
                "assets": assets,
            }

            return status

        except Exception as e:
            logger.error(f"Failed to get story status for {story_id}: {e}")
            return {"story_id": story_id, "status": "error", "error": str(e)}


# Global story service instance
story_service = StoryService()
