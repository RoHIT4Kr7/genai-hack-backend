"""
Nano-banana service with GCS storage and reference image support.
Combines Gemini 2.5 Flash Image Preview with Google Cloud Storage.
"""

import os
import base64
import asyncio
from typing import Optional, Dict, Any, List
from loguru import logger
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from google import genai
from google.cloud import storage
from config.settings import settings


class NanoBananaService:
    """
    Nano-banana service with mandatory features:
    1. Gemini 2.5 Flash Image Preview for image generation
    2. GCS storage with calmira-backend bucket
    3. Reference image generation for character consistency
    """

    def __init__(self):

        # Ensure we're using Google AI Studio, not Vertex AI
        os.environ.pop("GOOGLE_GENAI_USE_VERTEXAI", None)
        # Initialize Gemini API
        self.api_key = settings.gemini_api_key
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment")

        # Initialize nano-banana model using direct GenAI SDK (more reliable for images)
        self.genai_client = genai.Client(api_key=self.api_key)

        # Keep LangChain client for text generation if needed
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=self.api_key,
            temperature=0.7,
            max_output_tokens=4096,
        )

        # Initialize GCS client
        self.gcs_client = storage.Client()
        self.bucket_name = settings.gcs_bucket_name  # calmira-backend
        self.bucket = self.gcs_client.bucket(self.bucket_name)

        # Store reference images per story
        self.reference_images = {}

        logger.info(
            f"✅ Nano-banana service initialized with GCS bucket: {self.bucket_name}"
        )

    async def generate_reference_images(
        self, story_context: Dict[str, Any], story_id: str
    ) -> List[str]:
        """Generate reference images for character consistency."""
        try:
            logger.info(f"🎨 Generating reference images for story {story_id}")

            character_sheet = story_context.get("character_sheet", {})
            char_name = character_sheet.get("name", "Character")
            char_appearance = character_sheet.get("appearance", "anime character")
            char_age = character_sheet.get("age", "young adult")

            # ENHANCED ANIME CHARACTER REFERENCE PROMPT
            reference_prompt = f"""
ANIME CHARACTER DESIGN SHEET: Create a professional anime character reference for an original character named {char_name}.

**ORIGINAL CHARACTER SPECIFICATIONS:**
- **Name:** {char_name} (completely unique, not based on any existing anime character)
- **Physical Design:** {char_appearance}
- **Age Category:** {char_age}
- **Personality Traits:** Reflected through anime-style character design elements

**ANIME ART STYLE REQUIREMENTS:**
- **Visual Style:** High-quality anime character art with professional cel-shading and vibrant colors
- **Character Design:** Modern anime aesthetic with expressive features, detailed hair design, and authentic anime proportions
- **Color Palette:** Rich, vibrant anime colors with proper saturation and anime-style shading
- **Animation Quality:** Production-level anime character design suitable for animation reference

**REFERENCE SHEET LAYOUT:**
- **Primary View:** Full-body front view in neutral standing pose with clear anime proportions
- **Secondary View:** Side profile showing character design consistency and anime art style
- **Expression Guide:** Basic neutral expression with anime-style facial features
- **Design Consistency:** All views must show identical character with perfect anime art style

**TECHNICAL SPECIFICATIONS:**
- **Format:** Square 1:1 aspect ratio anime character sheet
- **Background:** Clean, simple background (light gray or white) to focus on character design
- **Quality:** Professional anime production quality with clean line art and proper shading
- **Style Consistency:** Maintain consistent anime aesthetic throughout all views

**CRITICAL CHARACTER ORIGINALITY:**
- Character design MUST be 100% original and unique
- NO resemblance to existing anime characters (Naruto, Luffy, Goku, Ichigo, etc.)
- Focus on creating a fresh, new anime character design
- Use anime art style and techniques without copying existing character designs

**RESTRICTIONS:**
- NO text, labels, speech bubbles, or captions on the character sheet
- NO existing anime franchise elements or symbols
- Character must be completely original while maintaining authentic anime aesthetic

This reference sheet will ensure perfect character consistency across all 6 anime story panels.
            """.strip()

            # Generate reference image using direct GenAI SDK
            response = await asyncio.to_thread(
                self.genai_client.models.generate_content,
                model="gemini-2.5-flash-image-preview",
                contents=[reference_prompt],
            )

            # Extract and upload reference image
            image_data = self._extract_image_from_response(response)
            ref_url = await self._upload_to_gcs(
                image_data, f"stories/{story_id}/reference_01.png"
            )

            # Store reference for this story
            self.reference_images[story_id] = [ref_url]

            logger.info(f"✅ Reference image generated: {ref_url}")
            return [ref_url]

        except Exception as e:
            logger.error(f"Failed to generate reference images: {e}")
            return []

    async def generate_panel_images_parallel(
        self, panels: List[Dict[str, Any]], story_id: str
    ) -> List[str]:
        """Generate all 6 panel images in parallel with reference consistency."""
        try:
            logger.info(f"🎨 Generating {len(panels)} panel images with nano-banana")

            # Step 1: Generate reference images first
            if panels:
                story_context = {
                    "character_sheet": panels[0].get("character_sheet", {}),
                    "prop_sheet": panels[0].get("prop_sheet", {}),
                    "style_guide": panels[0].get("style_guide", {}),
                }
                reference_urls = await self.generate_reference_images(
                    story_context, story_id
                )
            else:
                reference_urls = []

            # Step 2: Generate all panels in parallel
            panel_tasks = []
            for i, panel in enumerate(panels):
                task = self._generate_single_panel_with_reference(
                    panel, story_id, i + 1, reference_urls
                )
                panel_tasks.append(task)

            # Execute all panels in parallel
            panel_results = await asyncio.gather(*panel_tasks, return_exceptions=True)

            # Process results
            panel_urls = []
            for i, result in enumerate(panel_results):
                if isinstance(result, Exception):
                    logger.error(f"Panel {i+1} generation failed: {result}")
                    # Create fallback
                    fallback_url = await self._create_fallback_panel(story_id, i + 1)
                    panel_urls.append(fallback_url)
                else:
                    panel_urls.append(result)

            logger.info(f"✅ Generated {len(panel_urls)} panel images")
            return panel_urls

        except Exception as e:
            logger.error(f"Failed to generate panel images: {e}")
            raise

    async def _generate_single_panel_with_reference(
        self,
        panel_data: Dict[str, Any],
        story_id: str,
        panel_number: int,
        reference_urls: List[str],
    ) -> str:
        """Generate a single panel with reference consistency."""
        try:
            logger.info(f"Generating panel {panel_number} with reference consistency")

            # Create panel prompt with reference consistency
            panel_prompt = self._create_panel_prompt_with_reference(
                panel_data, panel_number, reference_urls
            )

            # Generate panel image using direct GenAI SDK
            response = await asyncio.to_thread(
                self.genai_client.models.generate_content,
                model="gemini-2.5-flash-image-preview",
                contents=[panel_prompt],
            )

            # Extract and upload panel image
            image_data = self._extract_image_from_response(response)
            panel_url = await self._upload_to_gcs(
                image_data, f"stories/{story_id}/panel_{panel_number:02d}.png"
            )

            logger.info(f"Panel {panel_number} generated: {panel_url}")

            # Emit real-time panel completion update
            try:
                from utils.socket_utils import emit_generation_progress

                await emit_generation_progress(
                    story_id=story_id,
                    event_type="panel_image_ready",
                    data={
                        "story_id": story_id,
                        "panel_number": panel_number,
                        "image_url": panel_url,
                        "status": "image_complete",
                    },
                )
                logger.info(f"📡 Emitted panel_image_ready for panel {panel_number}")
            except Exception as socket_error:
                logger.warning(f"Failed to emit panel update: {socket_error}")

            return panel_url

        except Exception as e:
            logger.error(f"Failed to generate panel {panel_number}: {e}")
            raise

    def _create_panel_prompt_with_reference(
        self, panel_data: Dict[str, Any], panel_number: int, reference_urls: List[str]
    ) -> str:
        """Create panel prompt with reference consistency."""

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

        # ENHANCED ANIME PANEL PROMPT
        prompt = f"""
ANIME PANEL {panel_number}: Professional anime scene featuring the EXACT SAME CHARACTER from the reference design.

**CHARACTER CONSISTENCY (CRITICAL):**
- Character MUST be identical to reference: {char_name} with {char_appearance}
- Maintain exact same anime character design: face, hair style, clothing, colors, and proportions
- Character should be instantly recognizable as the same anime character from reference
- Use consistent anime art style and character design throughout

**ANIME SCENE SPECIFICATIONS:**
- **Story Moment:** {framing} - a key emotional moment in {char_name}'s journey
- **Emotional State:** {emotional_tone} - character's expression and body language reflect this emotion
- **Character Thoughts:** "{dialogue_text}" - this internal state influences the character's anime expression
- **Narrative Purpose:** This scene advances {char_name}'s emotional growth and story development

**ANIME VISUAL STYLE:**
- **Art Quality:** High-definition anime illustration with professional cel-shading and vibrant colors
- **Animation Style:** Modern anime aesthetic with expressive character animation and detailed backgrounds
- **Color Grading:** Rich anime color palette with proper saturation, contrast, and anime-style lighting
- **Visual Effects:** Anime-specific atmospheric effects (particles, wind, lighting) that enhance the emotional tone

**ANIME COMPOSITION TECHNIQUES:**
- **Format:** Square 1:1 aspect ratio anime panel with cinematic composition
- **Camera Work:** Dynamic anime directing with appropriate angle and framing for emotional impact
- **Character Focus:** {char_name} is the clear focal point with anime-style emphasis techniques
- **Background Art:** Detailed anime background that supports the story and emotional atmosphere
- **Environmental Details:** Anime-style environmental elements that enhance the narrative

**ANIME ATMOSPHERIC EFFECTS:**
- **Lighting Style:** Anime-specific lighting with rim lighting, soft shadows, and emotional atmosphere
- **Particle Effects:** Appropriate anime effects (sparkles, wind, mist) based on emotional tone
- **Color Atmosphere:** Anime color grading that reflects {char_name}'s emotional journey
- **Environmental Animation:** Subtle anime environmental details (wind through hair, floating elements)

**TECHNICAL REQUIREMENTS:**
- **Animation Quality:** Production-level anime artwork suitable for professional animation
- **Character Art:** Maintain exact character design consistency with reference sheet
- **Style Consistency:** Pure anime aesthetic without mixing other art styles
- **Professional Finish:** Clean line art, proper shading, and anime-standard quality

**CRITICAL RESTRICTIONS:**
- NO text, speech bubbles, panel borders, or captions
- Character design must EXACTLY match the reference - no deviations
- Maintain pure anime art style without influence from other visual styles
- Focus on anime storytelling through visual composition and character expression

This is Panel {panel_number} of {char_name}'s 6-part anime story about resilience, hope, and personal growth.
        """.strip()

        return prompt

    def _extract_image_from_response(self, response) -> bytes:
        """Extract image data from direct GenAI SDK response."""
        try:
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
            logger.error(f"Failed to extract image from response: {e}")
            return self._create_placeholder_image_data()

    async def _upload_to_gcs(self, data: bytes, path: str) -> str:
        """Upload bytes to GCS and return signed URL."""
        try:
            blob = self.bucket.blob(path)
            blob.upload_from_string(data)

            # Generate signed URL (valid for 24 hours) since bucket has public access prevention
            from datetime import timedelta

            signed_url = blob.generate_signed_url(
                expiration=timedelta(hours=24), method="GET"
            )

            logger.info(f"Uploaded to GCS: {path} -> signed URL generated")
            return signed_url

        except Exception as e:
            logger.error(f"Failed to upload to GCS {path}: {e}")
            return ""

    def _create_placeholder_image_data(self) -> bytes:
        """Create placeholder image data."""
        from PIL import Image, ImageDraw
        import io

        # Create a simple placeholder image
        img = Image.new("RGB", (512, 512), color="lightgray")
        draw = ImageDraw.Draw(img)
        draw.text((200, 250), "Placeholder", fill="black")

        # Convert to bytes
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="PNG")
        return img_bytes.getvalue()

    async def _create_fallback_panel(self, story_id: str, panel_number: int) -> str:
        """Create fallback panel when generation fails."""
        try:
            logger.warning(f"Creating fallback panel {panel_number}")

            fallback_data = self._create_placeholder_image_data()
            fallback_url = await self._upload_to_gcs(
                fallback_data,
                f"stories/{story_id}/panel_{panel_number:02d}_fallback.png",
            )

            return fallback_url

        except Exception as e:
            logger.error(f"Failed to create fallback panel: {e}")
            return ""


# Global nano-banana service instance
nano_banana_service = NanoBananaService()
