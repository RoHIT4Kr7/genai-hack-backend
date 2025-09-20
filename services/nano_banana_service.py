"""
Nano-banana service with GCS storage and reference image support.
Combines Gemini 2.5 Flash Image Preview with Google Cloud Storage.
"""

import os
import base64
import asyncio
import time
from typing import Optional, Dict, Any, List
from loguru import logger
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from google import genai
from google.cloud import storage
from config.settings import settings


class ServiceMetrics:
    """Track service performance and errors."""

    def __init__(self):
        self.api_calls = 0
        self.successful_calls = 0
        self.failed_calls = 0
        self.errors = {}
        self.response_times = []

    def record_call(self, success: bool, response_time: float = 0, error: str = None):
        self.api_calls += 1
        if success:
            self.successful_calls += 1
            self.response_times.append(response_time)
        else:
            self.failed_calls += 1
            if error:
                self.errors[error] = self.errors.get(error, 0) + 1

    def get_stats(self) -> Dict[str, Any]:
        avg_response_time = (
            sum(self.response_times) / len(self.response_times)
            if self.response_times
            else 0
        )
        return {
            "total_calls": self.api_calls,
            "success_rate": (
                (self.successful_calls / self.api_calls * 100)
                if self.api_calls > 0
                else 0
            ),
            "failed_calls": self.failed_calls,
            "avg_response_time": avg_response_time,
            "common_errors": dict(
                sorted(self.errors.items(), key=lambda x: x[1], reverse=True)[:5]
            ),
        }


class NanoBananaService:
    """
    Nano-banana service with mandatory features:
    1. Gemini 2.5 Flash Image Preview for image generation
    2. GCS storage with hackathon-asset-genai bucket
    3. Reference image generation for character consistency
    4. Advanced rate limiting and retry logic to prevent 500 errors
    """

    def __init__(self):

        # Initialize metrics tracking
        self.metrics = ServiceMetrics()

        # Initialize rate limiting
        self._last_request_time = 0
        self._min_request_interval = 0.5  # Minimum 0.5 seconds between requests

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
        self.bucket_name = settings.gcs_bucket_name  # hackathon-asset-genai
        self.bucket = self.gcs_client.bucket(self.bucket_name)

        # Store reference images per story
        self.reference_images = {}

        logger.info(
            f"✅ Nano-banana service initialized with GCS bucket: {self.bucket_name}"
        )

    async def _apply_rate_limiting(self):
        """Apply rate limiting to prevent API overload and 500 errors."""
        current_time = time.time()
        time_since_last_request = current_time - self._last_request_time

        if time_since_last_request < self._min_request_interval:
            wait_time = self._min_request_interval - time_since_last_request
            logger.debug(f"⏱️  Rate limiting: waiting {wait_time:.2f}s...")
            await asyncio.sleep(wait_time)

        self._last_request_time = time.time()

    async def generate_reference_images(
        self, story_context: Dict[str, Any], story_id: str
    ) -> List[str]:
        """Generate reference images for character consistency using EXACT user inputs."""
        try:
            logger.info(f"🎨 Generating reference images for story {story_id}")

            character_sheet = story_context.get("character_sheet", {})
            char_name = character_sheet.get("name", "Character")
            char_appearance = character_sheet.get("appearance", "")
            char_age = character_sheet.get("age", "young adult")
            char_gender = character_sheet.get("gender", "")

            # ULTRA-AGGRESSIVE GENDER ENFORCEMENT FOR REFERENCE IMAGES
            gender_details = ""
            if char_gender.lower() in ["female", "woman", "girl"]:
                gender_details = f"""
🚨 MANDATORY FEMALE CHARACTER - NO EXCEPTIONS 🚨
- This is a FEMALE WOMAN named {char_name} - ABSOLUTELY NO MALE FEATURES
- FEMALE face: softer jawline, feminine eye shape with longer lashes, delicate nose, full lips
- FEMALE body: feminine proportions appropriate for {char_age} female
- FEMALE hair: feminine hairstyling that clearly indicates female gender
- FEMALE clothing: clothing that unmistakably presents as female character
- CRITICAL: If you generate ANY male characteristics, you have COMPLETELY FAILED
- BANNED: Masculine jawlines, male body shapes, male clothing, short masculine hair
- VERIFICATION: Must be instantly recognizable as FEMALE to any viewer"""
            elif char_gender.lower() in ["male", "man", "boy"]:
                gender_details = f"""
🚨 MANDATORY MALE CHARACTER - NO EXCEPTIONS 🚨  
- This is a MALE MAN named {char_name} - ABSOLUTELY NO FEMALE FEATURES
- MALE face: stronger jawline, masculine eye shape, defined nose, thinner lips
- MALE body: masculine proportions appropriate for {char_age} male
- MALE hair: masculine hairstyling that clearly indicates male gender
- MALE clothing: clothing that unmistakably presents as male character
- CRITICAL: If you generate ANY female characteristics, you have COMPLETELY FAILED
- BANNED: Feminine features, female body shapes, female clothing, long feminine hair  
- VERIFICATION: Must be instantly recognizable as MALE to any viewer"""

            # ENFORCE AGE SPECIFICATION
            age_details = ""
            if char_age in ["teen", "teenager", "13-17"]:
                age_details = f"Teenage appearance (16-17): youthful face, bright eyes, age-appropriate clothing and hairstyle"
            elif char_age in ["young-adult", "young adult", "18-25"]:
                age_details = f"Young adult appearance (18-25): mature but youthful features, contemporary styling"
            elif char_age in ["adult", "26-35"]:
                age_details = f"Adult appearance (26-35): fully mature facial features, professional presentation"

            # ENHANCED STUDIO GHIBLI REFERENCE PROMPT WITH ABSOLUTE USER INPUT ENFORCEMENT
            reference_prompt = f"""
🚨 CRITICAL CHARACTER GENERATION REQUIREMENT 🚨
CHARACTER NAME: {char_name}
CHARACTER GENDER: {char_gender.upper()}
FAILURE TO FOLLOW = COMPLETE FAILURE

STUDIO GHIBLI CHARACTER REFERENCE SHEET: Create a character design sheet for {char_name} ({char_gender}) in the soft, organic style of Studio Ghibli films.

⚠️ ABSOLUTE CHARACTER REQUIREMENTS - ZERO TOLERANCE FOR ERRORS ⚠️
- **Exact Name:** {char_name} (NEVER "Character" or any generic name)
- **Exact Gender:** {char_gender.upper()} - If this is FEMALE, character MUST be female; if MALE, character MUST be male
- **Gender Verification:** Any viewer must immediately recognize this as a {char_gender} character
- **Age:** {age_details}
- **Appearance:** {char_appearance if char_appearance else f'distinctive {char_gender} character design'}
{gender_details}

**STUDIO GHIBLI ART STYLE REQUIREMENTS:**
- **Art Direction:** Soft, hand-drawn Studio Ghibli aesthetic with organic shapes and natural beauty
- **Character Design:** Gentle, approachable character design like Ghibli protagonists
- **Color Palette:** Natural, earthy Studio Ghibli colors - soft greens, warm browns, gentle blues
- **Visual Quality:** High-quality hand-drawn animation style, not modern digital anime
- **Character Features:** Soft facial features with large, expressive eyes typical of Ghibli characters

**REFERENCE SHEET SPECIFICATIONS:**
- **Primary View:** Full-body front view of {char_name} in natural standing pose
- **Style Consistency:** 100% Studio Ghibli visual style throughout
- **Background:** Simple, natural background or plain color to focus on character
- **Expression:** Gentle, natural expression showing {char_name}'s personality

**FINAL VERIFICATION CHECKLIST:**
✅ Character is named {char_name} (not "Character" or generic name)
✅ Character is clearly {char_gender.upper()} with appropriate gender presentation
✅ Character matches Studio Ghibli art style (soft, organic, hand-drawn)
✅ Character has natural, age-appropriate appearance
✅ NO futuristic or sci-fi elements present

🚨 CRITICAL SUCCESS CRITERIA 🚨
If the generated character is NOT clearly identifiable as {char_name} the {char_gender}, then the generation has COMPLETELY FAILED.

Reference sheet for {char_name} ({char_gender}, {char_age}) in Studio Ghibli art style.
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
        """Generate all 6 panel images with staggered timing to avoid 500 errors."""
        try:
            logger.info(
                f"🎨 Generating {len(panels)} panel images with nano-banana and request spacing"
            )

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

                # Add spacing after reference generation
                logger.info("⏱️  Adding 2-second spacing after reference generation...")
                await asyncio.sleep(2)
            else:
                reference_urls = []

            # Step 2: Generate panels with staggered timing to prevent 500 errors
            panel_tasks = []
            for i, panel in enumerate(panels):
                # Add staggered delay to prevent overwhelming the API
                async def delayed_panel_task(panel_data, delay):
                    if delay > 0:
                        logger.info(
                            f"⏱️  Panel {delay//0.5 + 1}: Waiting {delay}s to prevent API overload..."
                        )
                        await asyncio.sleep(delay)
                    return await self._generate_single_panel_with_reference(
                        panel_data, story_id, int(delay // 0.5) + 1, reference_urls
                    )

                # Stagger requests by 0.5 seconds each
                delay = i * 0.5
                task = delayed_panel_task(panel, delay)
                panel_tasks.append(task)

            # Execute all panels with staggered timing
            logger.info("🚀 Starting staggered panel generation to avoid 500 errors...")
            panel_results = await asyncio.gather(*panel_tasks, return_exceptions=True)

            # Process results
            panel_urls = []
            for i, result in enumerate(panel_results):
                if isinstance(result, Exception):
                    logger.error(f"Panel {i+1} generation failed: {result}")
                    # Create fallback with error information
                    error_msg = (
                        str(result)[:50] + "..."
                        if len(str(result)) > 50
                        else str(result)
                    )
                    fallback_url = await self._create_fallback_panel(
                        story_id, i + 1, error_msg
                    )
                    panel_urls.append(fallback_url)
                else:
                    panel_urls.append(result)

            logger.info(
                f"✅ Generated {len(panel_urls)} panel images with staggered timing"
            )
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
        max_retries: int = 4,  # Increased retries for 500 errors
    ) -> str:
        """Generate a single panel with reference consistency and robust retry logic for 500 errors."""
        last_error = None
        start_time = time.time()

        for attempt in range(max_retries):
            try:
                attempt_start = time.time()
                logger.info(
                    f"Generating panel {panel_number} (attempt {attempt + 1}/{max_retries})"
                )

                # Create panel prompt with reference consistency
                panel_prompt = self._create_panel_prompt_with_reference(
                    panel_data, panel_number, reference_urls
                )

                # Enhanced exponential backoff for 500 errors
                if attempt > 0:
                    # Longer waits for 500 errors specifically
                    wait_time = min(2 ** (attempt + 1), 16)  # Cap at 16 seconds
                    logger.info(
                        f"⏱️  Waiting {wait_time}s before retry (handling server overload)..."
                    )
                    await asyncio.sleep(wait_time)

                # Add small pre-request delay to avoid overwhelming API
                if attempt == 0:
                    await asyncio.sleep(0.2)  # Small initial delay

                # Apply rate limiting to prevent 500 errors
                await self._apply_rate_limiting()

                # Generate panel image using direct GenAI SDK
                response = await asyncio.to_thread(
                    self.genai_client.models.generate_content,
                    model="gemini-2.5-flash-image-preview",
                    contents=[panel_prompt],
                )

                # Check if response has proper content
                if (
                    not response
                    or not hasattr(response, "candidates")
                    or not response.candidates
                ):
                    raise ValueError("Empty or invalid response from Gemini API")

                # Extract and upload panel image
                image_data = self._extract_image_from_response(response)
                if not image_data:
                    raise ValueError("No image data extracted from response")

                panel_url = await self._upload_to_gcs(
                    image_data, f"stories/{story_id}/panel_{panel_number:02d}.png"
                )

                # Record successful generation
                response_time = time.time() - attempt_start
                self.metrics.record_call(success=True, response_time=response_time)

                logger.info(
                    f"✅ Panel {panel_number} generated successfully: {panel_url} (took {response_time:.2f}s)"
                )

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
                    logger.info(
                        f"📡 Emitted panel_image_ready for panel {panel_number}"
                    )
                except Exception as socket_error:
                    logger.warning(f"Failed to emit panel update: {socket_error}")

                return panel_url

            except Exception as e:
                last_error = e
                error_type = type(e).__name__
                error_msg = str(e)

                logger.warning(
                    f"Panel {panel_number} attempt {attempt + 1} failed: {error_type}: {error_msg}"
                )

                # Enhanced error handling for 500 errors
                if (
                    "500" in error_msg
                    or "internal" in error_msg.lower()
                    or "overload" in error_msg.lower()
                ):
                    logger.warning(
                        f"🔄 Server overload detected for panel {panel_number}, will retry with backoff"
                    )
                    self.metrics.record_call(
                        success=False, error=f"server_500_error: {error_type}"
                    )

                    # Continue retrying for 500 errors (don't break)
                    if attempt == max_retries - 1:
                        logger.error(
                            f"❌ Panel {panel_number} failed after {max_retries} attempts due to persistent 500 errors"
                        )
                elif "quota" in error_msg.lower() or "billing" in error_msg.lower():
                    logger.error(
                        f"Non-retryable quota error for panel {panel_number}: {e}"
                    )
                    self.metrics.record_call(
                        success=False, error=f"quota_error: {error_type}"
                    )
                    break  # Don't retry quota errors
                else:
                    self.metrics.record_call(
                        success=False, error=f"other_error: {error_type}"
                    )

                    # For unknown errors, continue retrying but log it
                    logger.warning(
                        f"🔄 Unknown error for panel {panel_number}, will retry"
                    )

                # If this was the last attempt, break
                if attempt == max_retries - 1:
                    logger.error(
                        f"All {max_retries} attempts failed for panel {panel_number}"
                    )
                    break

        # If we get here, all retries failed
        total_time = time.time() - start_time
        logger.error(
            f"Failed to generate panel {panel_number} after {max_retries} attempts in {total_time:.2f}s. Last error: {last_error}"
        )

        # Log current service stats
        stats = self.metrics.get_stats()
        logger.info(f"Service stats: {stats}")

        raise last_error or Exception(f"Panel {panel_number} generation failed")

    def _create_panel_prompt_with_reference(
        self, panel_data: Dict[str, Any], panel_number: int, reference_urls: List[str]
    ) -> str:
        """Create panel prompt with STRICT character consistency enforcement."""

        dialogue_text = panel_data.get("dialogue_text", "")
        emotional_tone = panel_data.get("emotional_tone", "neutral")
        character_sheet = panel_data.get("character_sheet", {})

        # Panel-specific framing with focus on transformation in panels 5-6
        panel_framing = {
            1: f"Gentle introduction - establish {character_sheet.get('name', 'Character')} in their current daily environment",
            2: f"Moment of struggle - {character_sheet.get('name', 'Character')} facing a personal challenge or difficulty",
            3: f"Quiet reflection - {character_sheet.get('name', 'Character')} in thoughtful introspection about their situation",
            4: f"Building hope - {character_sheet.get('name', 'Character')} beginning to find inner strength or positive perspective",
            5: f"TRANSFORMATION MOMENT - {character_sheet.get('name', 'Character')} overcoming their challenge with inner strength and growth",
            6: f"INSPIRING CONCLUSION - {character_sheet.get('name', 'Character')} radiating confidence, wisdom, and motivational energy",
        }

        framing = panel_framing.get(
            panel_number,
            f"Story scene featuring {character_sheet.get('name', 'Character')}",
        )
        char_name = character_sheet.get("name", "Character")
        char_appearance = character_sheet.get("appearance", "")
        char_gender = character_sheet.get("gender", "")
        char_age = character_sheet.get("age", "young adult")

        # ULTRA-AGGRESSIVE GENDER CONSISTENCY ENFORCEMENT
        gender_enforcement = ""
        if char_gender.lower() in ["female", "woman", "girl"]:
            gender_enforcement = f"""
🚨 ABSOLUTE FEMALE CHARACTER REQUIREMENT 🚨
- {char_name} is a FEMALE WOMAN - NO EXCEPTIONS, NO COMPROMISES
- FEMALE ONLY: Female face, female body, female hair, female clothing
- BANNED: Any male features, masculine appearance, male clothing, male body shape
- ZERO TOLERANCE: If you generate a male character, you have FAILED completely
- VERIFICATION: Character must be obviously female to any viewer
- REFERENCE RULE: {char_name} MUST look exactly like the female reference image"""
        elif char_gender.lower() in ["male", "man", "boy"]:
            gender_enforcement = f"""
🚨 ABSOLUTE MALE CHARACTER REQUIREMENT 🚨
- {char_name} is a MALE MAN - NO EXCEPTIONS, NO COMPROMISES
- MALE ONLY: Male face, male body, male hair, male clothing
- BANNED: Any female features, feminine appearance, female clothing, female body shape
- ZERO TOLERANCE: If you generate a female character, you have FAILED completely
- VERIFICATION: Character must be obviously male to any viewer
- REFERENCE RULE: {char_name} MUST look exactly like the male reference image"""

        # ENHANCED STUDIO GHIBLI PANEL PROMPT WITH STRICT CONSISTENCY
        prompt = f"""STUDIO GHIBLI PANEL {panel_number}: Beautiful hand-drawn scene in Studio Ghibli art style featuring THE EXACT SAME CHARACTER from reference.

**CRITICAL CHARACTER CONSISTENCY - NO CHANGES ALLOWED:**
- **Character Identity:** {char_name} ({char_gender}, {char_age}) - MUST be 100% identical to reference design
- **Reference Matching:** Character MUST look exactly like the reference image - same face, hair, clothing, proportions
- **Gender Locked:** {char_gender} - CANNOT be changed, character must maintain exact gender presentation from reference
- **Zero Deviation:** Any change from reference character design is strictly forbidden
{gender_enforcement}

**STUDIO GHIBLI ART STYLE REQUIREMENTS:**
- **Art Direction:** Soft, organic Studio Ghibli aesthetic like Princess Mononoke, Spirited Away, or My Neighbor Totoro
- **Visual Quality:** Hand-drawn animation style with natural colors and gentle character design
- **Color Palette:** Natural Studio Ghibli colors - earthy tones, soft greens, warm light, never oversaturated
- **Character Integration:** {char_name} naturally integrated with beautiful, organic environment

**CHARACTER SPECIFICATIONS:**
- **Name:** {char_name} - exact same character from reference (never "Character" or generic names)
- **Appearance:** {char_appearance if char_appearance else 'matches reference sheet design exactly'}
- **Age Presentation:** {char_age} - must look exactly the same age as in reference
- **Consistency Rule:** Every visual detail must perfectly match the reference character

**STORY SCENE CONTEXT:**
- **Narrative Focus:** {framing} - showing {char_name}'s emotional journey in Studio Ghibli style
- **Emotional State:** {emotional_tone} - {char_name}'s gentle expression reflects this emotion naturally  
- **Inner Voice:** "{dialogue_text}" - this internal state influences {char_name}'s peaceful expression
- **Story Purpose:** Panel {panel_number} of 6 - meaningful moment in {char_name}'s personal growth

**STUDIO GHIBLI SCENE SPECIFICATIONS:**
- **Background:** Beautiful natural environment with Studio Ghibli's organic, atmospheric depth
- **Lighting:** Soft, natural lighting like sunlight through trees or warm golden hour light
- **Composition:** Gentle, harmonious composition showing {char_name} in natural harmony with environment
- **Atmosphere:** Peaceful, contemplative mood that supports the emotional storytelling

**CRITICAL RESTRICTIONS:**
- NO modern anime styling - only Studio Ghibli's soft, hand-drawn aesthetic
- NO gender changes - {char_name} must maintain exact gender from reference
- NO character design changes - identical face, hair, and clothing as reference
- NO futuristic or sci-fi elements - natural, organic Ghibli world only

Studio Ghibli Panel {panel_number}: {char_name} ({char_gender}) in a moment of {emotional_tone}, rendered with natural beauty and environmental harmony."""

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

    def _create_placeholder_image_data(
        self, panel_number: int = 1, error_info: str = None
    ) -> bytes:
        """Create informative placeholder image data."""
        from PIL import Image, ImageDraw, ImageFont
        import io

        # Create a professional-looking placeholder image
        img = Image.new("RGB", (1024, 1024), color="#2C3E50")
        draw = ImageDraw.Draw(img)

        try:
            # Try to use a better font if available
            font_large = ImageFont.truetype("arial.ttf", 60)
            font_medium = ImageFont.truetype("arial.ttf", 40)
            font_small = ImageFont.truetype("arial.ttf", 30)
        except:
            # Fallback to default font
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
            font_small = ImageFont.load_default()

        # Draw panel information
        draw.text(
            (512, 300),
            f"Panel {panel_number}",
            fill="#ECF0F1",
            font=font_large,
            anchor="mm",
        )
        draw.text(
            (512, 400),
            "Image Generation",
            fill="#BDC3C7",
            font=font_medium,
            anchor="mm",
        )
        draw.text(
            (512, 450),
            "Temporarily Unavailable",
            fill="#BDC3C7",
            font=font_medium,
            anchor="mm",
        )

        if error_info and len(error_info) < 50:
            draw.text(
                (512, 550),
                f"Reason: {error_info}",
                fill="#E74C3C",
                font=font_small,
                anchor="mm",
            )

        # Add a border
        draw.rectangle([10, 10, 1014, 1014], outline="#34495E", width=5)

        # Convert to bytes
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="PNG")
        return img_bytes.getvalue()

    def get_service_stats(self) -> Dict[str, Any]:
        """Get current service statistics."""
        return self.metrics.get_stats()

    def reset_metrics(self):
        """Reset service metrics."""
        self.metrics = ServiceMetrics()
        logger.info("Service metrics reset")

    async def _create_fallback_panel(
        self, story_id: str, panel_number: int, error_info: str = None
    ) -> str:
        """Create fallback panel when generation fails with better user feedback."""
        try:
            logger.warning(
                f"Creating fallback panel {panel_number} due to: {error_info or 'generation failure'}"
            )

            # Create a more informative fallback image
            fallback_data = self._create_placeholder_image_data(
                panel_number, error_info
            )
            fallback_url = await self._upload_to_gcs(
                fallback_data,
                f"stories/{story_id}/panel_{panel_number:02d}_fallback.png",
            )

            # Emit feedback about fallback creation
            try:
                from utils.socket_utils import emit_generation_progress

                await emit_generation_progress(
                    story_id=story_id,
                    event_type="panel_fallback",
                    data={
                        "story_id": story_id,
                        "panel_number": panel_number,
                        "image_url": fallback_url,
                        "status": "fallback_generated",
                        "reason": error_info or "Image generation failed",
                    },
                )
                logger.info(f"📡 Emitted panel_fallback for panel {panel_number}")
            except Exception as socket_error:
                logger.warning(f"Failed to emit fallback update: {socket_error}")

            return fallback_url

        except Exception as e:
            logger.error(f"Failed to create fallback panel: {e}")
            return ""


# Global nano-banana service instance
nano_banana_service = NanoBananaService()
