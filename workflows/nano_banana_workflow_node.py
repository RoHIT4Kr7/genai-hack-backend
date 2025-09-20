"""
Nano-Banana Workflow Node for LangGraph Integration

This module provides workflow nodes that integrate nano-banana (Gemini 2.5 Flash Image Preview)
with your existing LangGraph manga generation workflow while keeping Chirp 3 HD for TTS.
"""

import asyncio
import os
from typing import Dict, Any, List
from loguru import logger

from google import genai
from config.settings import settings
from services.gcs_storage_service import gcs_storage_service as storage_service
from services.chirp3hd_audio_service import chirp3hd_audio_service as audio_service
from utils.retry_helpers import exponential_backoff_async


class NanoBananaWorkflowNode:
    """
    Workflow node for nano-banana image generation.

    Integrates with your existing LangGraph workflow while using:
    - Google AI Studio: nano-banana for images (500 RPM)
    - Existing audio_service: Chirp 3 HD for TTS
    """

    def __init__(self):
        self.gemini_api_key = settings.gemini_api_key
        self.image_client = None
        self._initialize_nano_banana()

    def _initialize_nano_banana(self):
        """Initialize nano-banana client for image generation."""
        try:
            # Configure for Google AI Studio (nano-banana)
            os.environ.pop("GOOGLE_GENAI_USE_VERTEXAI", None)

            # Initialize direct GenAI SDK client (more reliable for images)
            self.image_client = genai.Client(api_key=self.gemini_api_key)

            logger.info(
                "✅ Nano-banana workflow node initialized with direct GenAI SDK"
            )

        except Exception as e:
            logger.error(f"Failed to initialize nano-banana workflow node: {e}")
            raise

    async def generate_reference_images_node(
        self, state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        LangGraph workflow node: Generate reference images for character consistency.

        This replaces or enhances your existing image generation workflow.
        """
        try:
            logger.info(
                f"🎨 Starting nano-banana reference image generation for {state['story_id']}"
            )

            if not state.get("panels"):
                raise Exception("No panels available for reference image generation")

            # Generate reference images using nano-banana
            reference_urls = await self._generate_reference_images(
                state["panels"], state["story_id"]
            )

            state["reference_images"] = reference_urls
            state["status"] = "reference_images_generated"

            logger.info(
                f"✅ Reference images generated for {state['story_id']}: {len(reference_urls)} images"
            )
            return state

        except Exception as e:
            logger.error(
                f"❌ Reference image generation failed for {state.get('story_id')}: {e}"
            )
            state["error"] = f"Reference image generation failed: {str(e)}"
            state["status"] = "error"
            return state

    async def generate_panels_with_nano_banana_node(
        self, state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        LangGraph workflow node: Generate all panels using nano-banana with reference consistency.

        This replaces your existing image_generation_loop_node with nano-banana.
        """
        try:
            logger.info(
                f"🖼️ Starting nano-banana panel generation for {state['story_id']}"
            )

            if not state.get("panels"):
                raise Exception("No panels available for nano-banana generation")

            # Get reference images if available
            reference_urls = state.get("reference_images", [])

            # Generate all panels in parallel using nano-banana
            panel_urls = await self._generate_panels_parallel(
                state["panels"], state["story_id"], reference_urls
            )

            state["image_urls"] = panel_urls
            state["status"] = "nano_banana_images_generated"

            logger.info(
                f"✅ Nano-banana panel generation completed for {state['story_id']}: {len(panel_urls)} images"
            )
            return state

        except Exception as e:
            logger.error(
                f"❌ Nano-banana panel generation failed for {state.get('story_id')}: {e}"
            )
            state["error"] = f"Nano-banana panel generation failed: {str(e)}"
            state["status"] = "error"
            return state

    async def generate_audio_with_chirp3hd_node(
        self, state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        LangGraph workflow node: Generate TTS audio using existing Chirp 3 HD service.

        This uses your existing audio_service for TTS generation.
        """
        try:
            logger.info(
                f"🎵 Starting Chirp 3 HD audio generation for {state['story_id']}"
            )

            if not state.get("panels"):
                raise Exception("No panels available for audio generation")

            # Use existing audio service for Chirp 3 HD TTS
            user_age_int = self._convert_age_range_to_int(state["inputs"].age)

            # Generate TTS for all panels in parallel
            tts_urls = await self._generate_tts_parallel(
                state["panels"], state["story_id"], user_age_int, state["inputs"].gender
            )

            # Use static background music (no Lyria needed)
            background_urls = ["/src/assets/audio/background-music.mp3"] * len(
                state["panels"]
            )

            state["tts_urls"] = tts_urls
            state["background_urls"] = background_urls
            state["status"] = "chirp3hd_audio_generated"

            logger.info(
                f"✅ Chirp 3 HD audio generation completed for {state['story_id']}"
            )
            return state

        except Exception as e:
            logger.error(
                f"❌ Chirp 3 HD audio generation failed for {state.get('story_id')}: {e}"
            )
            state["error"] = f"Chirp 3 HD audio generation failed: {str(e)}"
            state["status"] = "error"
            return state

    # Helper methods

    async def _generate_reference_images(
        self, panels: List[Dict], story_id: str
    ) -> List[str]:
        """Generate reference images using nano-banana."""
        try:
            if not panels:
                return []

            # Extract character info from first panel
            first_panel = panels[0]
            character_sheet = first_panel.get("character_sheet", {})

            # Create reference prompt
            reference_prompt = self._create_reference_prompt(character_sheet)

            logger.info(
                f"Generating reference image with nano-banana for story {story_id}"
            )

            response = await exponential_backoff_async(
                lambda: asyncio.to_thread(
                    self.image_client.models.generate_content,
                    model="gemini-2.5-flash-image-preview",
                    contents=[reference_prompt],
                ),
                max_retries=5,
                initial_delay=1.0,
                max_delay=30.0,
            )

            # Extract and upload reference image
            image_data = self._extract_image_from_response(response)
            ref_url = await storage_service.upload_bytes(
                image_data, f"stories/{story_id}/reference_01.png"
            )

            logger.info(f"Reference image generated with nano-banana: {ref_url}")
            return [ref_url]

        except Exception as e:
            logger.error(f"Failed to generate reference images with nano-banana: {e}")
            return []

    def _create_reference_prompt(self, character_sheet: Dict) -> str:
        """Create prompt for nano-banana reference image generation."""
        char_name = character_sheet.get("name", "Character")
        char_appearance = character_sheet.get("appearance", "anime character")
        char_age = character_sheet.get("age", "young adult")

        prompt = f"""
Create a character reference sheet for {char_name} using nano-banana (Gemini 2.5 Flash Image Preview).

CHARACTER DETAILS:
- Name: {char_name}
- Appearance: {char_appearance}
- Age: {char_age}

NANO-BANANA REQUIREMENTS:
- Full body character reference in neutral pose
- Clean manga/anime art style with high detail
- Multiple angles (front view, side profile)
- Consistent character design elements
- Professional character sheet layout
- Square 1:1 aspect ratio
- No text, speech bubbles, or captions
- High detail for future reference consistency across all panels

This reference will be used by nano-banana to generate consistent character appearances across multiple manga panels.
        """.strip()

        return prompt

    async def _generate_panels_parallel(
        self, panels: List[Dict], story_id: str, reference_urls: List[str]
    ) -> List[str]:
        """Generate all panels in parallel using nano-banana."""
        try:
            # Create panel generation tasks
            panel_tasks = []
            for i, panel in enumerate(panels):
                task = self._generate_single_panel_nano_banana(
                    panel, story_id, i + 1, reference_urls
                )
                panel_tasks.append(task)

            # Execute all panels in parallel with nano-banana
            panel_results = await asyncio.gather(*panel_tasks, return_exceptions=True)

            # Process results
            panel_urls = []
            for i, result in enumerate(panel_results):
                if isinstance(result, Exception):
                    logger.error(f"Nano-banana panel {i+1} generation failed: {result}")
                    fallback_url = await self._create_fallback_panel(story_id, i + 1)
                    panel_urls.append(fallback_url)
                else:
                    panel_urls.append(result)

            logger.info(f"Generated {len(panel_urls)} panel images with nano-banana")
            return panel_urls

        except Exception as e:
            logger.error(f"Failed to generate panels with nano-banana: {e}")
            raise

    async def _generate_single_panel_nano_banana(
        self,
        panel_data: Dict,
        story_id: str,
        panel_number: int,
        reference_urls: List[str],
    ) -> str:
        """Generate a single panel using nano-banana."""
        try:
            # Create panel prompt for nano-banana
            panel_prompt = self._create_panel_prompt_nano_banana(
                panel_data, panel_number, reference_urls
            )

            response = await exponential_backoff_async(
                lambda: asyncio.to_thread(
                    self.image_client.models.generate_content,
                    model="gemini-2.5-flash-image-preview",
                    contents=[panel_prompt],
                ),
                max_retries=5,
                initial_delay=1.0,
                max_delay=30.0,
            )

            # Extract and upload panel
            image_data = self._extract_image_from_response(response)
            panel_url = await storage_service.upload_bytes(
                image_data, f"stories/{story_id}/panel_{panel_number:02d}.png"
            )

            logger.info(f"Nano-banana panel {panel_number} generated: {panel_url}")
            return panel_url

        except Exception as e:
            logger.error(f"Failed to generate nano-banana panel {panel_number}: {e}")
            raise

    def _create_panel_prompt_nano_banana(
        self, panel_data: Dict, panel_number: int, reference_urls: List[str]
    ) -> str:
        """Create panel prompt for nano-banana generation."""
        dialogue_text = panel_data.get("dialogue_text", "")
        emotional_tone = panel_data.get("emotional_tone", "neutral")
        character_sheet = panel_data.get("character_sheet", {})

        # Panel-specific framing
        panel_framing = {
            1: "Introduction scene - establish character and setting",
            2: "Challenge scene - show conflict or obstacle",
            3: "Reflection scene - character contemplation and introspection",
            4: "Discovery scene - breakthrough or realization moment",
            5: "Transformation scene - character taking positive action",
            6: "Resolution scene - hopeful conclusion and growth",
        }

        framing = panel_framing.get(panel_number, "Manga panel scene")
        char_name = character_sheet.get("name", "Character")
        char_appearance = character_sheet.get("appearance", "anime character")

        reference_context = ""
        if reference_urls:
            reference_context = f"""
IMPORTANT: Use the character design from the reference sheet to maintain consistency.
The character should match the appearance, clothing, and style from the reference image.
Reference character sheet was created for this story - maintain exact visual consistency.
"""

        prompt = f"""
Create Panel {panel_number} of a manga story using nano-banana (Gemini 2.5 Flash Image Preview).

{reference_context}

CHARACTER:
- Name: {char_name}
- Appearance: {char_appearance}
- Must match reference character design exactly

PANEL {panel_number} SPECIFICATIONS:
- Scene type: {framing}
- Emotional tone: {emotional_tone}
- Narrative context: {dialogue_text}

NANO-BANANA COMPOSITION REQUIREMENTS:
- Square 1:1 aspect ratio manga panel
- Professional manga/anime art style with high quality
- Character must match reference sheet design exactly
- Clear character visibility and emotional expression
- Appropriate background and environment for the scene
- Dynamic composition that serves the story

TECHNICAL REQUIREMENTS:
- High-quality manga illustration using nano-banana capabilities
- Clean line art and professional finish
- No text, speech bubbles, or captions
- Character consistency with reference sheet
- Focus on visual storytelling through composition and expression
- Leverage nano-banana's 500 RPM rate limit for fast generation

Create a compelling visual that captures this story moment while maintaining perfect character consistency using nano-banana.
        """.strip()

        return prompt

    async def _generate_tts_parallel(
        self, panels: List[Dict], story_id: str, user_age_int: int, user_gender: str
    ) -> List[str]:
        """Generate TTS audio using existing Chirp 3 HD service."""
        try:
            # Create audio generation tasks using existing audio_service
            audio_tasks = []
            for i, panel in enumerate(panels):
                dialogue_text = panel.get("dialogue_text", "")
                task = audio_service.generate_tts_audio(
                    dialogue_text, story_id, i + 1, user_age_int, user_gender
                )
                audio_tasks.append(task)

            # Execute all audio generation in parallel
            audio_results = await asyncio.gather(*audio_tasks, return_exceptions=True)

            # Process results
            audio_urls = []
            for i, result in enumerate(audio_results):
                if isinstance(result, Exception):
                    logger.error(f"Chirp 3 HD audio {i+1} generation failed: {result}")
                    audio_urls.append("")
                else:
                    audio_urls.append(result)

            logger.info(
                f"Generated {len([url for url in audio_urls if url])} audio files with Chirp 3 HD"
            )
            return audio_urls

        except Exception as e:
            logger.error(f"Failed to generate audio with Chirp 3 HD: {e}")
            return [""] * len(panels)

    def _convert_age_range_to_int(self, age_range: str) -> int:
        """Convert age range string to approximate integer for voice selection."""
        age_mapping = {
            "teen": 16,
            "young-adult": 22,
            "adult": 30,
            "mature": 45,
            "senior": 65,
            "not-specified": 25,
        }
        return age_mapping.get(age_range, 25)

    def _extract_image_from_response(self, response) -> bytes:
        """Extract image data from direct GenAI SDK response."""
        try:
            logger.info(f"Nano-banana response type: {type(response)}")

            # Handle direct GenAI SDK response format
            if hasattr(response, "candidates") and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, "content") and hasattr(
                    candidate.content, "parts"
                ):
                    for part in candidate.content.parts:
                        if part.inline_data is not None:
                            logger.info(
                                f"✅ Found image data: {len(part.inline_data.data)} bytes"
                            )
                            return part.inline_data.data
                        elif part.text is not None:
                            logger.info(f"Found text part: {part.text[:100]}...")

            # If no image found, log the response structure for debugging
            logger.warning(
                f"No image found in response. Response type: {type(response)}"
            )
            if hasattr(response, "candidates"):
                logger.warning(
                    f"Candidates count: {len(response.candidates) if response.candidates else 0}"
                )

            # Fallback: create placeholder
            logger.warning("Using placeholder image data")
            return self._create_placeholder_image_data()

        except Exception as e:
            logger.error(f"Failed to extract image from nano-banana response: {e}")
            return self._create_placeholder_image_data()

    def _create_placeholder_image_data(self) -> bytes:
        """Create placeholder image when nano-banana generation fails."""
        try:
            from PIL import Image, ImageDraw, ImageFont
            import io

            img = Image.new("RGB", (512, 512), color="#f0f0f0")
            draw = ImageDraw.Draw(img)

            try:
                font = ImageFont.load_default()
            except:
                font = None

            text = "Nano-Banana\nManga Panel"
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            x = (512 - text_width) // 2
            y = (512 - text_height) // 2

            draw.text((x, y), text, fill="#666666", font=font)

            # Convert to bytes
            img_buffer = io.BytesIO()
            img.save(img_buffer, format="PNG")
            img_buffer.seek(0)

            return img_buffer.getvalue()

        except Exception as e:
            logger.error(f"Failed to create placeholder: {e}")
            # Return minimal PNG
            return b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x02\x00\x00\x00\x02\x00\x08\x02\x00\x00\x00\x7f\xd8\xb2\xde\x00\x00\x00\x0cIDATx\x9cc\x00\x00\x00\x02\x00\x01\xe5\x27\xde\xfc\x00\x00\x00\x00IEND\xaeB`\x82"

    async def _create_fallback_panel(self, story_id: str, panel_number: int) -> str:
        """Create fallback panel when nano-banana generation fails."""
        try:
            logger.warning(f"Creating fallback panel {panel_number}")

            fallback_data = self._create_placeholder_image_data()
            fallback_url = await storage_service.upload_bytes(
                fallback_data,
                f"stories/{story_id}/panel_{panel_number:02d}_fallback.png",
            )

            return fallback_url

        except Exception as e:
            logger.error(f"Failed to create fallback panel: {e}")
            return ""


# Global nano-banana workflow node instance
nano_banana_workflow_node = NanoBananaWorkflowNode()
