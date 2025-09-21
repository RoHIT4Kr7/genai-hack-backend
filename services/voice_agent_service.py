"""
PyAudio-Free Voice Agent Service
Handles client-side audio via WebSocket streaming
"""

import os
import asyncio
import base64
import numpy as np
from typing import Optional, Callable, Dict, Any
from loguru import logger
from fastapi import WebSocket, WebSocketDisconnect
from google import genai
from google.genai import types
import json

# Remove all PyAudio dependencies
# All audio processing now handled client-side

# Audio configuration constants (for reference only)
SEND_SAMPLE_RATE = 16000
RECEIVE_SAMPLE_RATE = 24000
CHANNELS = 1

# Ensure Google AI Studio usage
os.environ.pop("GOOGLE_GENAI_USE_VERTEXAI", None)

# Initialize Gemini client
client = genai.Client(
    http_options={"api_version": "v1beta"},
    api_key=os.environ.get("GEMINI_API_KEY"),
)

# Voice agent configuration
VOICE_CONFIG = types.LiveConnectConfig(
    response_modalities=["AUDIO", "TEXT"],  # Support both audio and text
    speech_config=types.SpeechConfig(
        language_code="en-US",
        voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Zephyr")
        ),
    ),
    system_instruction=types.Content(
        parts=[
            types.Part.from_text(
                text="""You are a helpful AI assistant for anime and manga creation.
                Provide creative guidance, character development ideas, and storytelling advice.
                Respond naturally and conversationally, keeping responses concise but helpful.
                Be encouraging and supportive while offering practical creative suggestions."""
            )
        ],
        role="user",
    ),
)


class WebSocketVoiceAgent:
    """PyAudio-free Voice Agent using WebSocket streaming."""

    def __init__(self):
        self.active_sessions: Dict[str, Dict[str, Any]] = {}

    async def create_session(self, session_id: str, websocket: WebSocket):
        """Create a new voice session with WebSocket connection."""
        try:
            logger.info(f"🎤 Creating voice session: {session_id}")

            # Validate API key
            api_key = os.environ.get("GEMINI_API_KEY")
            if not api_key:
                logger.error("❌ GEMINI_API_KEY environment variable is not set")
                raise ValueError("GEMINI_API_KEY environment variable is not set")

            logger.info(f"✅ GEMINI_API_KEY is configured")

            # Create Gemini Live session
            logger.info(f"🤖 Connecting to Gemini Live API...")
            session_context = client.aio.live.connect(
                model="models/gemini-2.5-flash-live-preview", config=VOICE_CONFIG
            )
            session = await asyncio.wait_for(session_context.__aenter__(), timeout=15.0)
            logger.info(f"✅ Connected to Gemini Live API")

            # Store session data
            self.active_sessions[session_id] = {
                "session": session,
                "session_context": session_context,
                "websocket": websocket,
                "is_running": True,
                "audio_queue": asyncio.Queue(maxsize=100),
            }

            # Start session tasks
            logger.info(f"🔄 Starting session tasks for {session_id}")
            await self._start_session_tasks(session_id)

            logger.success(f"✅ Voice session created successfully: {session_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to create session {session_id}: {e}")
            logger.error(f"❌ Exception type: {type(e).__name__}")
            logger.error(f"❌ Exception details: {str(e)}")
            return False

    async def handle_audio_data(self, session_id: str, audio_data: bytes):
        """Handle incoming audio data from client."""
        session_data = self.active_sessions.get(session_id)
        if not session_data or not session_data["is_running"]:
            return

        try:
            # Convert raw audio bytes to the format expected by Gemini Live API
            # Client sends Int16 PCM data at 16 kHz mono
            # Use the SDK's InputAudioBuffer and include sample rate in the mime type
            audio_message = types.InputAudioBuffer(
                mime_type=f"audio/pcm;rate={SEND_SAMPLE_RATE}", data=audio_data
            )

            # Send to Gemini Live API
            await session_data["session"].send(input=audio_message)

        except Exception as e:
            logger.error(f"Error handling audio data for {session_id}: {e}")

    async def handle_text_message(self, session_id: str, message: str):
        """Handle incoming text message from client."""
        session_data = self.active_sessions.get(session_id)
        if not session_data or not session_data["is_running"]:
            return False

        try:
            await session_data["session"].send(input=message, end_of_turn=True)
            return True
        except Exception as e:
            logger.error(f"Error sending text message for {session_id}: {e}")
            return False

    async def end_turn(self, session_id: str) -> bool:
        """Explicitly end the current user turn to trigger model response."""
        session_data = self.active_sessions.get(session_id)
        if not session_data or not session_data.get("session"):
            return False
        try:
            await session_data["session"].send(end_of_turn=True)
            return True
        except Exception as e:
            logger.error(f"Error ending turn for {session_id}: {e}")
            return False

    async def stop_session(self, session_id: str):
        """Stop a voice session."""
        if session_id not in self.active_sessions:
            return

        session_data = self.active_sessions[session_id]
        session_data["is_running"] = False

        try:
            # Cancel session tasks
            if hasattr(session_data, "tasks"):
                for task in session_data["tasks"]:
                    if not task.done():
                        task.cancel()
                await asyncio.gather(*session_data["tasks"], return_exceptions=True)

            # Close Gemini session
            if session_data.get("session_context"):
                await session_data["session_context"].__aexit__(None, None, None)

            # Remove from active sessions
            del self.active_sessions[session_id]

            logger.success(f"Session stopped: {session_id}")

        except Exception as e:
            logger.error(f"Error stopping session {session_id}: {e}")

    async def _start_session_tasks(self, session_id: str):
        """Start background tasks for session."""
        session_data = self.active_sessions[session_id]

        # Create response handler task
        response_task = asyncio.create_task(self._handle_responses(session_id))
        session_data["tasks"] = [response_task]

    async def _handle_responses(self, session_id: str):
        """Handle responses from Gemini Live API."""
        session_data = self.active_sessions.get(session_id)
        if not session_data:
            return

        websocket = session_data["websocket"]

        try:
            while session_data["is_running"]:
                if not session_data.get("session"):
                    break

                try:
                    turn = session_data["session"].receive()
                    async for response in turn:
                        if not session_data["is_running"]:
                            break

                        # Handle audio response
                        if hasattr(response, "data") and response.data:
                            # Convert audio data to base64 for transmission
                            audio_b64 = base64.b64encode(response.data).decode("utf-8")

                            await websocket.send_text(
                                json.dumps(
                                    {
                                        "type": "audio_response",
                                        "session_id": session_id,
                                        "audio_data": audio_b64,
                                        "mime_type": f"audio/pcm;rate={RECEIVE_SAMPLE_RATE}",
                                        "timestamp": self._get_timestamp(),
                                    }
                                )
                            )

                        # Handle text response
                        if hasattr(response, "text") and response.text:
                            await websocket.send_text(
                                json.dumps(
                                    {
                                        "type": "ai_response",
                                        "session_id": session_id,
                                        "text": response.text,
                                        "timestamp": self._get_timestamp(),
                                    }
                                )
                            )

                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.warning(f"Response handling error for {session_id}: {e}")
                    await asyncio.sleep(0.1)

        except Exception as e:
            logger.error(f"Response handler failed for {session_id}: {e}")

    def _get_timestamp(self):
        """Get current timestamp."""
        from datetime import datetime

        return datetime.now().isoformat()


# Global service instance
voice_agent = WebSocketVoiceAgent()


# Legacy compatibility - keeping the old class name for existing imports
class VoiceAgentService(WebSocketVoiceAgent):
    """Legacy compatibility wrapper."""

    pass


# Global voice agent service instance (for backward compatibility)
voice_agent_service = voice_agent
