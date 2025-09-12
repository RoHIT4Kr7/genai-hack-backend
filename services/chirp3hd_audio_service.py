"""
Chirp 3 HD TTS service with age/gender-based voice selection.
"""

import asyncio
from typing import List, Dict, Any, Tuple
from loguru import logger
from google.cloud import texttospeech
from config.settings import settings
from services.gcs_storage_service import gcs_storage_service


class Chirp3HDAudioService:
    """Chirp 3 HD TTS service with personalized voice selection."""

    def __init__(self):
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize Google Cloud TTS client."""
        try:
            # Initialize TTS client using GOOGLE_APPLICATION_CREDENTIALS
            self.client = texttospeech.TextToSpeechClient()
            logger.info("✅ Chirp 3 HD TTS service initialized")

        except Exception as e:
            logger.error(f"Failed to initialize Chirp 3 HD TTS: {e}")
            raise

    def _select_voice(self, user_age: int, user_gender: str) -> Dict[str, str]:
        """Select appropriate voice based on user age and gender."""
        try:
            # Age-based voice selection
            if user_age <= 18:
                # Teen voices
                if user_gender.lower() in ["female", "woman", "girl"]:
                    voice_name = "en-US-Journey-F"  # Young female voice
                elif user_gender.lower() in ["male", "man", "boy"]:
                    voice_name = "en-US-Journey-D"  # Young male voice
                else:
                    voice_name = "en-US-Journey-F"  # Default to female for non-binary
            elif user_age <= 30:
                # Young adult voices
                if user_gender.lower() in ["female", "woman", "girl"]:
                    voice_name = "en-US-Journey-F"
                elif user_gender.lower() in ["male", "man", "boy"]:
                    voice_name = "en-US-Journey-D"
                else:
                    voice_name = "en-US-Journey-O"  # Neutral voice
            else:
                # Adult voices
                if user_gender.lower() in ["female", "woman", "girl"]:
                    voice_name = "en-US-Studio-O"  # Mature female voice
                elif user_gender.lower() in ["male", "man", "boy"]:
                    voice_name = "en-US-Studio-M"  # Mature male voice
                else:
                    voice_name = "en-US-Studio-O"  # Default to neutral

            voice_config = {
                "language_code": "en-US",
                "name": voice_name,
                "ssml_gender": texttospeech.SsmlVoiceGender.NEUTRAL,
            }

            logger.info(
                f"Selected voice for age {user_age}, gender {user_gender}: {voice_name}"
            )
            return voice_config

        except Exception as e:
            logger.error(f"Voice selection failed: {e}")
            # Fallback to default voice
            return {
                "language_code": "en-US",
                "name": "en-US-Journey-F",
                "ssml_gender": texttospeech.SsmlVoiceGender.NEUTRAL,
            }

    async def generate_tts_audio(
        self,
        text: str,
        story_id: str,
        panel_number: int,
        user_age: int,
        user_gender: str,
    ) -> str:
        """Generate TTS audio for a panel using Chirp 3 HD."""
        try:
            if not text or not text.strip():
                logger.warning(f"Empty text for panel {panel_number}, skipping TTS")
                return ""

            # Select appropriate voice
            voice_config = self._select_voice(user_age, user_gender)

            # Create voice selection
            voice = texttospeech.VoiceSelectionParams(
                language_code=voice_config["language_code"],
                name=voice_config["name"],
                ssml_gender=voice_config["ssml_gender"],
            )

            # Create synthesis input
            synthesis_input = texttospeech.SynthesisInput(text=text)

            # Create audio config for high quality
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=0.9,  # Slightly slower for better comprehension
                pitch=0.0,
                volume_gain_db=0.0,
                sample_rate_hertz=24000,  # High quality
            )

            # Generate speech
            logger.info(
                f"Generating TTS for panel {panel_number} with voice {voice_config['name']}"
            )
            response = await asyncio.to_thread(
                self.client.synthesize_speech,
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config,
            )

            # Upload to GCS
            audio_path = f"stories/{story_id}/tts_{panel_number:02d}.mp3"
            audio_url = await gcs_storage_service.upload_bytes(
                response.audio_content, audio_path
            )

            logger.info(f"TTS generated for panel {panel_number}: {audio_url}")
            return audio_url

        except Exception as e:
            logger.error(f"Failed to generate TTS for panel {panel_number}: {e}")
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
                bg_url = f"https://storage.googleapis.com/{settings.gcs_bucket_name}/stories/{story_id}/bg_{i+1:02d}.mp3"
                background_urls.append(bg_url)

            logger.info(
                f"Generated {len(processed_tts_urls)} TTS files and {len(background_urls)} background URLs"
            )
            return background_urls, processed_tts_urls

        except Exception as e:
            logger.error(f"Failed to generate all audio: {e}")
            return [], []


# Global Chirp 3 HD audio service instance
chirp3hd_audio_service = Chirp3HDAudioService()
