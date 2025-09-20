"""
Chirp 3 HD TTS service with age/gender-based voice selection.
Mandatory feature for proper dialogue generation.
"""

import asyncio
import time
from typing import List, Dict, Any, Tuple
from loguru import logger
from google.cloud import texttospeech
from config.settings import settings


class TTSMetrics:
    """Track TTS service performance."""

    def __init__(self):
        self.tts_calls = 0
        self.successful_calls = 0
        self.failed_calls = 0
        self.audio_durations = []
        self.processing_times = []

    def record_tts_call(
        self, success: bool, processing_time: float = 0, audio_duration: float = 0
    ):
        self.tts_calls += 1
        if success:
            self.successful_calls += 1
            self.processing_times.append(processing_time)
            if audio_duration > 0:
                self.audio_durations.append(audio_duration)
        else:
            self.failed_calls += 1


class Chirp3HDTTSService:
    """Chirp 3 HD TTS service with personalized voice selection."""

    def __init__(self):
        self.client = texttospeech.TextToSpeechClient()
        self.bucket_name = settings.gcs_bucket_name  # hackathon-asset-genai
        self.metrics = TTSMetrics()
        logger.info("✅ Chirp 3 HD TTS service initialized")

    def _select_voice(self, user_age: int, user_gender: str) -> Dict[str, str]:
        """Select appropriate voice based on user age and gender with Chirp 3 HD voices."""
        try:
            # Age-based voice selection with Chirp 3 HD voice mapping
            # Age ranges: 13-17 (teen), 18-25 (young-adult), 26-35 (adult)

            if user_age <= 17:  # 13-17 age range
                if user_gender.lower() in ["female", "woman", "girl"]:
                    voice_name = "en-IN-Chirp3-HD-Kore"  # Female teen voice
                elif user_gender.lower() in ["male", "man", "boy"]:
                    voice_name = "en-IN-Chirp3-HD-Puck"  # Male teen voice
                else:
                    voice_name = "en-IN-Chirp3-HD-Kore"  # Default to female

            elif user_age <= 25:  # 18-25 age range
                if user_gender.lower() in ["female", "woman", "girl"]:
                    voice_name = "en-IN-Chirp3-HD-Erinome"  # Female young adult voice
                elif user_gender.lower() in ["male", "man", "boy"]:
                    voice_name = "en-IN-Chirp3-HD-Achird"  # Male young adult voice
                else:
                    voice_name = "en-IN-Chirp3-HD-Erinome"  # Default to female

            elif user_age <= 35:  # 26-35 age range
                if user_gender.lower() in ["female", "woman", "girl"]:
                    voice_name = "en-IN-Chirp3-HD-Callirrhoe"  # Female adult voice
                elif user_gender.lower() in ["male", "man", "boy"]:
                    voice_name = "en-IN-Chirp3-HD-Alnilam"  # Male adult voice
                else:
                    voice_name = "en-IN-Chirp3-HD-Callirrhoe"  # Default to female

            else:
                # Fallback for ages above 35 (shouldn't happen with new frontend but keeping for safety)
                if user_gender.lower() in ["female", "woman", "girl"]:
                    voice_name = "en-IN-Chirp3-HD-Callirrhoe"  # Use adult female voice
                elif user_gender.lower() in ["male", "man", "boy"]:
                    voice_name = "en-IN-Chirp3-HD-Alnilam"  # Use adult male voice
                else:
                    voice_name = "en-IN-Chirp3-HD-Callirrhoe"  # Default to female

            voice_config = {
                "language_code": "en-IN",
                "name": voice_name,
                "ssml_gender": texttospeech.SsmlVoiceGender.NEUTRAL,
            }

            logger.info(
                f"Selected Chirp 3 HD voice for age {user_age}, gender {user_gender}: {voice_name}"
            )
            return voice_config

        except Exception as e:
            logger.error(f"Voice selection failed: {e}")
            # Fallback to default Chirp 3 HD voice
            return {
                "language_code": "en-IN",
                "name": "en-IN-Chirp3-HD-Kore",  # Default to Kore
                "ssml_gender": texttospeech.SsmlVoiceGender.NEUTRAL,
            }

    def _clean_text_for_tts(self, text: str) -> str:
        """Clean text for better TTS pronunciation and 8-10 second duration."""
        import re

        # Remove the "dialogue text: " or "dialogue_text: " prefix that may be included by the LLM
        # This handles both space and underscore variations: "dialogue text:", "dialogue_text:", etc.
        text = re.sub(
            r'^dialogue[\s_]*text[\s_]*:\s*["\']?', "", text, flags=re.IGNORECASE
        )

        # Remove quotes and special characters that don't help with narration
        text = text.strip("\"'")

        # Remove action descriptions in brackets/parentheses
        text = re.sub(r"\[.*?\]", "", text)
        text = re.sub(r"\(.*?\)", "", text)

        # Replace underscores with spaces (common issue causing "underscore" to be read)
        text = text.replace("_", " ")

        # Replace other problematic symbols with natural alternatives
        text = text.replace("&", " and ")
        text = text.replace("%", " percent ")
        text = text.replace("#", " number ")
        text = text.replace("@", " at ")
        text = text.replace("*", " ")
        text = text.replace("+", " plus ")
        text = text.replace("=", " equals ")
        text = text.replace("<", " less than ")
        text = text.replace(">", " greater than ")
        text = text.replace("/", " or ")
        text = text.replace("\\", " ")
        text = text.replace("|", " ")
        text = text.replace("^", " ")
        text = text.replace("~", " ")
        text = text.replace("`", "")

        # Handle multiple consecutive symbols or numbers
        text = re.sub(r'[^\w\s\.,!?;:\'"-]', " ", text)

        # Replace em dashes and special punctuation with natural pauses
        text = text.replace("—", ", ")
        text = text.replace("–", ", ")
        text = text.replace("...", ". ")
        text = text.replace("..", ". ")

        # Clean up multiple spaces and normalize punctuation
        text = re.sub(r"\s+", " ", text)
        text = text.replace(" ,", ",").replace(" .", ".")
        text = text.replace(" !", "!").replace(" ?", "?")
        text = text.replace(" ;", ";").replace(" :", ":")

        # Ensure proper sentence ending for natural speech
        text = text.strip()
        if text and not text.endswith((".", "!", "?")):
            text += "."

        # Limit length for 8-10 second duration (approximately 25-35 words)
        words = text.split()
        if len(words) > 35:
            # Take first 35 words and ensure it ends properly
            text = " ".join(words[:35])
            if not text.endswith((".", "!", "?")):
                text += "."

        # Final cleanup to ensure natural flow
        text = re.sub(r"\s+", " ", text).strip()

        logger.info(f"Cleaned TTS text: '{text}'")
        return text

    def _normalize_text_length(self, text: str) -> str:
        """Normalize text length for consistent audio duration across panels."""
        words = text.split()
        target_words = 30  # Target 30 words for consistent ~8-10 second duration

        if len(words) < 15:  # Too short - but don't add generic content
            logger.warning(f"TTS text too short ({len(words)} words): '{text}'")
            # Instead of adding generic text, just ensure proper ending
            if not text.strip().endswith((".", "!", "?")):
                text = text.strip() + "."

        elif len(words) > 40:  # Too long
            # Truncate to target length while maintaining meaning
            text = " ".join(words[:target_words])
            if not text.endswith((".", "!", "?")):
                text += "."

        return text

    async def generate_tts_audio(
        self,
        text: str,
        story_id: str,
        panel_number: int,
        user_age: int,
        user_gender: str,
    ) -> str:
        """Generate TTS audio for a panel using Chirp 3 HD."""
        start_time = time.time()

        try:
            if not text or not text.strip():
                logger.warning(f"Empty text for panel {panel_number}, skipping TTS")
                return ""

            # Clean text for better TTS and proper duration (consistent across all panels)
            cleaned_text = self._clean_text_for_tts(text)

            # Ensure consistent length for similar audio duration across panels
            cleaned_text = self._normalize_text_length(cleaned_text)

            logger.info(f"Panel {panel_number} normalized TTS text: '{cleaned_text}'")

            # Select appropriate voice
            voice_config = self._select_voice(user_age, user_gender)

            # Create voice selection
            voice = texttospeech.VoiceSelectionParams(
                language_code=voice_config["language_code"],
                name=voice_config["name"],
                ssml_gender=voice_config["ssml_gender"],
            )

            # Create synthesis input with cleaned text
            synthesis_input = texttospeech.SynthesisInput(text=cleaned_text)

            # Create audio config for high quality Chirp 3 HD with consistent settings
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=0.9,  # Consistent rate for all panels (8-10 seconds)
                pitch=0.0,  # Neutral pitch for consistency
                volume_gain_db=2.0,  # Consistent volume boost for clarity
                sample_rate_hertz=24000,  # High quality, consistent sample rate
                # Add effects profile for consistency
                effects_profile_id=["small-bluetooth-speaker-class-device"],
            )

            # Generate speech
            logger.info(
                f"Generating Chirp 3 HD TTS for panel {panel_number} with voice {voice_config['name']}"
            )
            response = await asyncio.to_thread(
                self.client.synthesize_speech,
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config,
            )

            processing_time = time.time() - start_time

            # Upload to GCS (using nano-banana service's GCS client)
            from services.nano_banana_service import nano_banana_service

            audio_path = f"stories/{story_id}/tts_{panel_number:02d}.mp3"
            audio_url = await nano_banana_service._upload_to_gcs(
                response.audio_content, audio_path
            )

            # Estimate audio duration (rough calculation: ~150 words per minute)
            word_count = len(cleaned_text.split())
            estimated_duration = (word_count / 150) * 60  # seconds

            # Record successful TTS generation
            self.metrics.record_tts_call(
                success=True,
                processing_time=processing_time,
                audio_duration=estimated_duration,
            )

            logger.info(
                f"✅ Chirp 3 HD TTS generated for panel {panel_number}: {audio_url} "
                f"(processed in {processing_time:.2f}s, ~{estimated_duration:.1f}s audio)"
            )

            # Emit real-time audio completion update
            try:
                from utils.socket_utils import emit_generation_progress

                await emit_generation_progress(
                    story_id=story_id,
                    event_type="panel_audio_ready",
                    data={
                        "story_id": story_id,
                        "panel_number": panel_number,
                        "audio_url": audio_url,
                        "status": "audio_complete",
                    },
                )
                logger.info(f"📡 Emitted panel_audio_ready for panel {panel_number}")
            except Exception as socket_error:
                logger.warning(f"Failed to emit audio update: {socket_error}")

            return audio_url

        except Exception as e:
            processing_time = time.time() - start_time
            self.metrics.record_tts_call(success=False, processing_time=processing_time)

            logger.error(
                f"Failed to generate Chirp 3 HD TTS for panel {panel_number} after {processing_time:.2f}s: {e}"
            )
            return ""

    async def generate_all_audio(
        self,
        panels: List[Dict[str, Any]],
        story_id: str,
        user_age: int,
        user_gender: str,
    ) -> Tuple[List[str], List[str]]:
        """Generate all audio for panels."""
        try:
            # Generate TTS for all panels in parallel
            tts_tasks = []
            for i, panel in enumerate(panels):
                dialogue_text = panel.get("dialogue_text", "")
                task = self.generate_tts_audio(
                    dialogue_text, story_id, i + 1, user_age, user_gender
                )
                tts_tasks.append(task)

            # Execute all TTS generation in parallel
            tts_urls = await asyncio.gather(*tts_tasks, return_exceptions=True)

            # Process results and handle exceptions
            processed_tts_urls = []
            for i, result in enumerate(tts_urls):
                if isinstance(result, Exception):
                    logger.error(f"TTS generation failed for panel {i+1}: {result}")
                    processed_tts_urls.append("")
                else:
                    processed_tts_urls.append(result)

            # Generate background music URLs (static for now)
            background_urls = []
            for i in range(len(panels)):
                bg_url = f"https://storage.googleapis.com/{self.bucket_name}/stories/{story_id}/bg_{i+1:02d}.mp3"
                background_urls.append(bg_url)

            logger.info(
                f"Generated {len(processed_tts_urls)} Chirp 3 HD TTS files and {len(background_urls)} background URLs"
            )
            return background_urls, processed_tts_urls

        except Exception as e:
            logger.error(f"Failed to generate all audio: {e}")
            return [], []

    def get_tts_stats(self) -> Dict[str, Any]:
        """Get current TTS service statistics."""
        avg_processing_time = (
            sum(self.metrics.processing_times) / len(self.metrics.processing_times)
            if self.metrics.processing_times
            else 0
        )
        avg_audio_duration = (
            sum(self.metrics.audio_durations) / len(self.metrics.audio_durations)
            if self.metrics.audio_durations
            else 0
        )

        return {
            "total_tts_calls": self.metrics.tts_calls,
            "success_rate": (
                (self.metrics.successful_calls / self.metrics.tts_calls * 100)
                if self.metrics.tts_calls > 0
                else 0
            ),
            "failed_calls": self.metrics.failed_calls,
            "avg_processing_time": avg_processing_time,
            "avg_audio_duration": avg_audio_duration,
        }


# Global Chirp 3 HD TTS service instance
chirp3hd_tts_service = Chirp3HDTTSService()
