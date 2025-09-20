"""
Dhyaan (Meditation) Service with Gemini 2.5 Flash TTS integration.
"""

import os
import json
import uuid
import asyncio
import mimetypes
import struct
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from pathlib import Path

from google import genai
from google.genai import types
from langchain_google_genai import ChatGoogleGenerativeAI
from google.cloud import storage
from loguru import logger

from config.settings import settings


class DhyaanService:
    """Meditation service with Gemini 2.5 Flash TTS and personalized content generation."""

    def __init__(self):
        # Ensure we're using Google AI Studio, not Vertex AI
        os.environ.pop("GOOGLE_GENAI_USE_VERTEXAI", None)

        self.api_key = settings.gemini_api_key
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")

        # Initialize Gemini AI client for TTS
        self.genai_client = genai.Client(api_key=self.api_key)

        # Initialize LLM for meditation script generation
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=self.api_key,
            temperature=0.7,
            max_output_tokens=4096,
        )

        # Initialize GCS for storing generated meditation audio
        self.gcs_client = storage.Client()
        self.bucket_name = settings.gcs_bucket_name  # hackathon-asset-genai
        self.bucket = self.gcs_client.bucket(self.bucket_name)

        # Load meditation music metadata
        self._load_music_metadata()

        logger.info("✅ DhyaanService initialized with Gemini 2.5 Flash TTS")

    def _load_music_metadata(self):
        """Load meditation music metadata from JSON file."""
        try:
            metadata_path = (
                Path(__file__).parent.parent
                / "config"
                / "meditation_music_metadata.json"
            )

            if not metadata_path.exists():
                logger.warning(
                    f"Meditation music metadata file not found at: {metadata_path}"
                )
                self.music_metadata = {}
                return

            with open(metadata_path, "r") as f:
                self.music_metadata = json.load(f)
            logger.info(f"✅ Meditation music metadata loaded from {metadata_path}")
            logger.debug(f"Loaded {len(self.music_metadata)} music combinations")
        except Exception as e:
            logger.error(f"Failed to load meditation music metadata: {e}")
            self.music_metadata = {}

    def _get_system_prompt(self) -> str:
        """Get the meditation script generation system prompt."""
        return """You are a Meditation Script Generator AI. Your task is to generate guided meditation scripts that follow these rules:

🔹 Style Guide (Mandatory)
• Write in a soothing, compassionate, and calming tone.
• Use ellipses (…) inline for short pauses.
• Use a single line with … for medium pauses.
• Use multiple blank lines + … for long pauses.
• Do not use [pause], <break>, or any markup tags.
• Keep sentences short and flowing, like natural spoken meditation guidance.

🔹 Personalization Rules
Adapt the script based on the user's inputs:

• currentFeeling → Acknowledge and gently address this state at the start. Example:
  - If "anxious": "I know you may be feeling anxious right now… but we will gently guide the mind toward calm."
  - If "lonely": "If you are feeling alone right now… let this practice remind you of connection."

• desiredFeeling → Guide the meditation toward this outcome. Example:
  - If "peaceful": emphasize stillness and calm imagery.
  - If "happy": add uplifting, energizing imagery.
  - If "confident": include empowerment and self-affirmation themes.

• experience → Adjust language and complexity:
  - Beginner: Keep instructions simple, very step-by-step, with more reassurance.
  - Intermediate: Slightly deeper cues, fewer reminders.
  - Advanced: More open-ended, less hand-holding, more silent pauses.

🔹 Structure Guidelines
• Begin with acknowledging the current feeling
• Guide through gentle breathing awareness
• Include body awareness or visualization appropriate to desired feeling
• End with affirmations related to the desired emotional state
• Include natural pauses for reflection

Remember: Your words will be spoken aloud, so write for the ear, not the eye."""

    def _get_music_info(
        self, current_feeling: str, desired_feeling: str
    ) -> Dict[str, Any]:
        """Get music file information based on user feelings."""
        # Simple lookup using the new format: currentFeeling_desiredFeeling
        music_key = f"{current_feeling.lower()}_{desired_feeling.lower()}"

        if music_key in self.music_metadata:
            music_data = self.music_metadata[music_key]
            return {
                "filename": f"{music_key}.mp3",
                "gcs_path": music_data["file"],
                "duration_seconds": music_data["duration"],
                "description": f"Meditation music for transitioning from {current_feeling} to {desired_feeling}",
                "best_for": music_data["bestFor"],
                "target": music_data["target"],
            }

        # Fallback to default duration if specific combination not found
        logger.warning(f"Music combination {music_key} not found, using default")
        return {
            "filename": f"{music_key}.mp3",
            "gcs_path": f"gs://hackathon-asset-genai/meditative-music/{music_key}.mp3",
            "duration_seconds": 480,  # 8 minutes default
            "description": f"Meditation music for transitioning from {current_feeling} to {desired_feeling}",
            "best_for": [current_feeling],
            "target": [desired_feeling],
        }

    def _create_meditation_prompt(
        self,
        current_feeling: str,
        desired_feeling: str,
        experience: str,
        duration_seconds: int,
    ) -> str:
        """Create personalized meditation prompt based on user inputs."""
        duration_minutes = duration_seconds // 60

        prompt = f"""Generate a {duration_minutes}-minute guided meditation script for someone who:

Current Feeling: {current_feeling}
Desired Feeling: {desired_feeling}  
Experience Level: {experience}

The meditation should last approximately {duration_seconds} seconds when spoken aloud.

Please create a complete guided meditation script that acknowledges their current state of feeling {current_feeling} and gently guides them toward feeling {desired_feeling}. 

Adjust the complexity and guidance style for a {experience} practitioner.

Include natural speaking pauses and breathing spaces throughout the script."""

        return prompt

    async def _generate_meditation_script(
        self,
        current_feeling: str,
        desired_feeling: str,
        experience: str,
        duration_seconds: int,
    ) -> str:
        """Generate personalized meditation script using Gemini."""
        try:
            system_prompt = self._get_system_prompt()
            user_prompt = self._create_meditation_prompt(
                current_feeling, desired_feeling, experience, duration_seconds
            )

            # Create messages for the LLM
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]

            # Generate meditation script
            response = await asyncio.to_thread(
                self.llm.invoke,
                [{"role": msg["role"], "content": msg["content"]} for msg in messages],
            )

            script = response.content
            logger.info(f"✅ Generated meditation script ({len(script)} characters)")
            return script

        except Exception as e:
            logger.error(f"Failed to generate meditation script: {e}")
            raise

    def _convert_to_wav(self, audio_data: bytes, mime_type: str) -> bytes:
        """Converts audio data to WAV format with proper header."""
        parameters = self._parse_audio_mime_type(mime_type)
        bits_per_sample = parameters["bits_per_sample"]
        sample_rate = parameters["rate"]
        num_channels = 1
        data_size = len(audio_data)
        bytes_per_sample = bits_per_sample // 8
        block_align = num_channels * bytes_per_sample
        byte_rate = sample_rate * block_align
        chunk_size = 36 + data_size

        header = struct.pack(
            "<4sI4s4sIHHIIHH4sI",
            b"RIFF",  # ChunkID
            chunk_size,  # ChunkSize
            b"WAVE",  # Format
            b"fmt ",  # Subchunk1ID
            16,  # Subchunk1Size
            1,  # AudioFormat (PCM)
            num_channels,  # NumChannels
            sample_rate,  # SampleRate
            byte_rate,  # ByteRate
            block_align,  # BlockAlign
            bits_per_sample,  # BitsPerSample
            b"data",  # Subchunk2ID
            data_size,  # Subchunk2Size
        )
        return header + audio_data

    def _parse_audio_mime_type(self, mime_type: str) -> Dict[str, int]:
        """Parse bits per sample and rate from audio MIME type."""
        bits_per_sample = 16
        rate = 24000

        parts = mime_type.split(";")
        for param in parts:
            param = param.strip()
            if param.lower().startswith("rate="):
                try:
                    rate_str = param.split("=", 1)[1]
                    rate = int(rate_str)
                except (ValueError, IndexError):
                    pass
            elif param.startswith("audio/L"):
                try:
                    bits_per_sample = int(param.split("L", 1)[1])
                except (ValueError, IndexError):
                    pass

        return {"bits_per_sample": bits_per_sample, "rate": rate}

    async def _generate_audio_with_tts(self, script: str) -> bytes:
        """Generate audio from meditation script using Gemini 2.5 Flash TTS."""
        try:
            logger.info("🎵 Generating meditation audio with Gemini TTS...")

            # TTS speaking style instructions combined with script
            tts_instructions = """Read this script in a soothing meditation style.
Speak slowly, with a warm and gentle tone.
Pause naturally between phrases, and linger longer when ellipses (…) appear.
When you see multiple ellipses or blank lines, let there be a deeper pause, as if giving space for the listener to breathe.
Keep the delivery calm, compassionate, and nurturing, like a meditation teacher.

Here is the meditation script to read:

"""

            # Combine instructions with the actual script
            full_tts_content = tts_instructions + script

            # Configure TTS generation with single user message
            contents = [
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=full_tts_content)],
                ),
            ]

            generate_content_config = types.GenerateContentConfig(
                temperature=0.8,  # Slightly more controlled for consistent meditation voice
                response_modalities=["audio"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name="Zephyr"  # Calm, soothing voice
                        )
                    )
                ),
            )

            # Generate audio in chunks
            audio_data = b""

            for chunk in self.genai_client.models.generate_content_stream(
                model="gemini-2.5-flash-preview-tts",
                contents=contents,
                config=generate_content_config,
            ):
                if (
                    chunk.candidates is None
                    or chunk.candidates[0].content is None
                    or chunk.candidates[0].content.parts is None
                ):
                    continue

                if (
                    chunk.candidates[0].content.parts[0].inline_data
                    and chunk.candidates[0].content.parts[0].inline_data.data
                ):

                    inline_data = chunk.candidates[0].content.parts[0].inline_data
                    data_buffer = inline_data.data

                    # Convert to WAV if needed
                    file_extension = mimetypes.guess_extension(inline_data.mime_type)
                    if file_extension is None:
                        data_buffer = self._convert_to_wav(
                            inline_data.data, inline_data.mime_type
                        )

                    audio_data += data_buffer

            if not audio_data:
                raise Exception("No audio data generated from TTS")

            logger.info(f"✅ Generated meditation audio ({len(audio_data)} bytes)")
            return audio_data

        except Exception as e:
            logger.error(f"Failed to generate meditation audio: {e}")
            raise

    async def _upload_audio_to_gcs(self, audio_data: bytes, meditation_id: str) -> str:
        """Upload generated audio to GCS and return signed URL."""
        try:
            # Create path for meditation audio
            audio_path = f"meditation-audio/{meditation_id}.wav"
            blob = self.bucket.blob(audio_path)

            # Upload audio data
            await asyncio.to_thread(blob.upload_from_string, audio_data)

            # Generate signed URL (valid for 24 hours)
            signed_url = await asyncio.to_thread(
                blob.generate_signed_url, expiration=timedelta(hours=24), method="GET"
            )

            logger.info(f"✅ Uploaded meditation audio to GCS: {audio_path}")
            return signed_url

        except Exception as e:
            logger.error(f"Failed to upload meditation audio to GCS: {e}")
            raise

    async def _get_background_music_url(self, gcs_path: str) -> str:
        """Get signed URL for background music from GCS."""
        try:
            # Extract blob path from GCS URI
            blob_path = gcs_path.replace(f"gs://{self.bucket_name}/", "")
            blob = self.bucket.blob(blob_path)

            # Generate signed URL for background music
            signed_url = await asyncio.to_thread(
                blob.generate_signed_url, expiration=timedelta(hours=24), method="GET"
            )

            return signed_url

        except Exception as e:
            logger.warning(f"Could not get background music URL: {e}")
            return ""

    async def generate_meditation(
        self, current_feeling: str, desired_feeling: str, experience: str
    ) -> Dict[str, Any]:
        """
        Generate personalized meditation with audio and background music.

        Args:
            current_feeling: User's current emotional state
            desired_feeling: What they want to feel
            experience: Meditation experience level (beginner/intermediate/advanced)

        Returns:
            Dictionary containing meditation details and URLs
        """
        try:
            # Validate inputs
            if not current_feeling or not desired_feeling or not experience:
                raise ValueError(
                    "All fields (current feeling, desired feeling, experience) are required"
                )

            # Check if service is properly initialized
            if not hasattr(self, "genai_client") or not self.genai_client:
                raise ValueError("Gemini AI client is not properly initialized")

            if not hasattr(self, "llm") or not self.llm:
                raise ValueError("Language model is not properly initialized")

            logger.info(
                f"🧘 Generating meditation: {current_feeling} → {desired_feeling} ({experience})"
            )

            # Generate unique meditation ID
            meditation_id = f"med_{uuid.uuid4().hex[:8]}"

            # Get music information for this feeling combination
            music_info = self._get_music_info(current_feeling, desired_feeling)
            duration_seconds = music_info["duration_seconds"]

            # Generate meditation script and audio in parallel with music URL
            script_task = asyncio.create_task(
                self._generate_meditation_script(
                    current_feeling, desired_feeling, experience, duration_seconds
                )
            )

            music_url_task = asyncio.create_task(
                self._get_background_music_url(music_info["gcs_path"])
            )

            # Wait for script generation
            script = await script_task

            # Generate audio from script
            audio_data = await self._generate_audio_with_tts(script)

            # Upload audio and get music URL in parallel
            audio_upload_task = asyncio.create_task(
                self._upload_audio_to_gcs(audio_data, meditation_id)
            )

            background_music_url = await music_url_task
            audio_url = await audio_upload_task

            # Create meditation title
            title = f"From {current_feeling.title()} to {desired_feeling.title()}: A Gentle Journey"

            # Determine guidance type based on desired feeling
            guidance_type_map = {
                "peaceful": "breathing",
                "calm": "body_scan",
                "happy": "visualization",
                "confident": "affirmation",
                "connected": "loving_kindness",
            }
            guidance_type = guidance_type_map.get(desired_feeling.lower(), "breathing")

            # Return meditation data
            result = {
                "meditation_id": meditation_id,
                "title": title,
                "duration": duration_seconds,
                "audio_url": audio_url,
                "script": script,
                "background_music_url": background_music_url,
                "guidance_type": guidance_type,
                "created_at": datetime.utcnow().isoformat() + "Z",
            }

            logger.info(f"✅ Successfully generated meditation: {meditation_id}")
            return result

        except Exception as e:
            logger.error(f"Failed to generate meditation: {e}")
            # Provide more specific error information
            if "API key" in str(e).lower():
                raise ValueError("Gemini API key is not configured properly")
            elif "quota" in str(e).lower() or "limit" in str(e).lower():
                raise ValueError("API quota exceeded. Please try again later")
            elif "network" in str(e).lower() or "connection" in str(e).lower():
                raise ValueError(
                    "Network connection error. Please check your internet connection"
                )
            else:
                raise ValueError(f"Meditation generation failed: {str(e)}")


# Global service instance
try:
    dhyaan_service = DhyaanService()
    logger.info("✅ DhyaanService global instance created successfully")
except Exception as e:
    logger.error(f"❌ Failed to create DhyaanService global instance: {e}")
    dhyaan_service = None
