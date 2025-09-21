"""
PyAudio-Free Voice Agent Service - Fixed Version
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
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Audio configuration constants (for reference only)
SEND_SAMPLE_RATE = 16000
RECEIVE_SAMPLE_RATE = 24000
CHANNELS = 1

# Ensure Google AI Studio usage
os.environ.pop("GOOGLE_GENAI_USE_VERTEXAI", None)

# Validate and initialize API key
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    logger.error("❌ GEMINI_API_KEY environment variable is not set")
    logger.error("Please set your Gemini API key in .env file or environment variables")
    client = None
else:
    logger.info(f"✅ GEMINI_API_KEY loaded: {api_key[:10]}...{api_key[-4:]}")
    try:
        # Initialize Gemini client
        client = genai.Client(
            http_options={"api_version": "v1beta"},
            api_key=api_key,
        )
        logger.info("✅ Gemini client initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Gemini client: {e}")
        client = None

# Voice agent configuration - FIXED to include both modalities
VOICE_CONFIG = types.LiveConnectConfig(
    response_modalities=["AUDIO", "TEXT"],  # Enable both audio and text responses
    speech_config=types.SpeechConfig(
        voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Aoede")
        ),
    ),
    system_instruction=types.Content(
        parts=[
            types.Part.from_text(
                text="You are a helpful AI assistant. Respond naturally and conversationally, keeping responses concise but helpful."
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

            # Validate client is available
            if not client:
                error_msg = (
                    "Gemini client not initialized - check GEMINI_API_KEY configuration"
                )
                logger.error(f"❌ {error_msg}")
                await self._send_error_to_client(websocket, error_msg)
                return False

            # Validate API key
            api_key = os.environ.get("GEMINI_API_KEY")
            if not api_key:
                error_msg = "GEMINI_API_KEY environment variable is not set"
                logger.error(f"❌ {error_msg}")
                await self._send_error_to_client(websocket, error_msg)
                return False

            logger.info(f"✅ Using API key: {api_key[:10]}...{api_key[-4:]}")

            # Create Gemini Live session with proper timeout and error handling
            logger.info(f"🤖 Connecting to Gemini Live API...")
            try:
                session_context = client.aio.live.connect(
                    model="models/gemini-2.5-flash-live-preview",  # Use stable model
                    config=VOICE_CONFIG,
                )
                session = await asyncio.wait_for(
                    session_context.__aenter__(), timeout=20.0  # Increased timeout
                )
                logger.info(f"✅ Connected to Gemini Live API successfully")
            except asyncio.TimeoutError:
                error_msg = "Timeout connecting to Gemini Live API - check your API key and network connection"
                logger.error(f"❌ {error_msg}")
                await self._send_error_to_client(websocket, error_msg)
                return False
            except Exception as e:
                error_msg = f"Failed to connect to Gemini Live API: {str(e)}"
                logger.error(f"❌ {error_msg}")
                await self._send_error_to_client(websocket, error_msg)
                return False

            # Store session data with enhanced tracking
            self.active_sessions[session_id] = {
                "session": session,
                "session_context": session_context,
                "websocket": websocket,
                "is_running": True,
                "audio_queue": asyncio.Queue(maxsize=100),
                "retry_count": 0,
                "last_activity": asyncio.get_event_loop().time(),
                "connected_at": asyncio.get_event_loop().time(),
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

            await self._send_error_to_client(
                websocket, f"Session creation failed: {str(e)}"
            )
            return False

    async def _send_error_to_client(self, websocket: WebSocket, error_message: str):
        """Send error message to client via WebSocket."""
        try:
            await websocket.send_text(
                json.dumps(
                    {
                        "type": "error",
                        "message": error_message,
                        "timestamp": self._get_timestamp(),
                    }
                )
            )
            logger.info(f"Sent error to client: {error_message}")
        except Exception as e:
            logger.warning(f"Failed to send error to client: {e}")

    async def handle_audio_data(self, session_id: str, audio_data: bytes):
        """Handle incoming audio data from client."""
        session_data = self.active_sessions.get(session_id)
        if not session_data or not session_data["is_running"]:
            return

        try:
            # Update last activity timestamp
            session_data["last_activity"] = asyncio.get_event_loop().time()

            # Check if session is still valid
            if not session_data.get("session"):
                logger.warning(f"Session {session_id} has no active Gemini session")
                return

            # Send raw PCM audio data to Gemini Live API
            # The audio data is already in the correct Int16 PCM format from client
            await session_data["session"].send(input=audio_data)
            logger.debug(
                f"Audio data sent to Gemini for {session_id}: {len(audio_data)} bytes"
            )

            # Reset retry count on successful send
            session_data["retry_count"] = 0

        except Exception as e:
            logger.error(f"Error handling audio data for {session_id}: {e}")
            # Increment retry count and check for session health
            session_data["retry_count"] = session_data.get("retry_count", 0) + 1
            if session_data["retry_count"] > 5:
                logger.error(
                    f"Too many audio failures for {session_id}, stopping session"
                )
                session_data["is_running"] = False

    async def handle_text_message(self, session_id: str, message: str):
        """Handle incoming text message from client."""
        session_data = self.active_sessions.get(session_id)
        if not session_data or not session_data["is_running"]:
            return False

        try:
            # Update last activity timestamp
            session_data["last_activity"] = asyncio.get_event_loop().time()

            if not session_data.get("session"):
                logger.warning(f"Session {session_id} has no active Gemini session")
                return False

            await session_data["session"].send(input=message, end_of_turn=True)
            logger.info(
                f"Text message sent to Gemini for {session_id}: {message[:50]}..."
            )

            # Reset retry count on successful send
            session_data["retry_count"] = 0
            return True
        except Exception as e:
            logger.error(f"Error sending text message for {session_id}: {e}")
            # Increment retry count and check for session health
            session_data["retry_count"] = session_data.get("retry_count", 0) + 1
            if session_data["retry_count"] > 3:
                logger.error(
                    f"Too many text failures for {session_id}, stopping session"
                )
                session_data["is_running"] = False
            return False

    async def stop_session(self, session_id: str):
        """Stop a voice session."""
        if session_id not in self.active_sessions:
            return

        session_data = self.active_sessions[session_id]
        session_data["is_running"] = False

        try:
            # Cancel session tasks
            if "tasks" in session_data:
                for task in session_data["tasks"]:
                    if not task.done():
                        task.cancel()
                await asyncio.gather(*session_data["tasks"], return_exceptions=True)

            # Close Gemini session
            if session_data.get("session_context"):
                try:
                    await session_data["session_context"].__aexit__(None, None, None)
                except Exception as e:
                    logger.warning(f"Error closing Gemini session context: {e}")

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
                    logger.warning(
                        f"No session for {session_id}, stopping response handler"
                    )
                    break

                try:
                    # Check WebSocket connection
                    if not self._is_websocket_connected(websocket):
                        logger.info(
                            f"WebSocket closed for {session_id}, stopping response handler"
                        )
                        session_data["is_running"] = False
                        break

                    # Receive turn from Gemini with timeout
                    try:
                        turn = session_data["session"].receive()

                        # Process each response in the turn
                        async for response in turn:
                            if not session_data["is_running"]:
                                break

                            # Double-check WebSocket state
                            if not self._is_websocket_connected(websocket):
                                logger.info(
                                    f"WebSocket closed during response for {session_id}"
                                )
                                session_data["is_running"] = False
                                break

                            try:
                                # Handle audio response
                                if hasattr(response, "data") and response.data:
                                    # Convert audio data to base64 for transmission
                                    audio_b64 = base64.b64encode(response.data).decode(
                                        "utf-8"
                                    )

                                    await websocket.send_text(
                                        json.dumps(
                                            {
                                                "type": "audio_response",
                                                "session_id": session_id,
                                                "audio_data": audio_b64,
                                                "timestamp": self._get_timestamp(),
                                            }
                                        )
                                    )
                                    logger.debug(
                                        f"Audio response sent for {session_id}"
                                    )

                                # Handle text response (now possible with TEXT modality enabled)
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
                                    logger.info(
                                        f"Text response sent for {session_id}: {response.text[:50]}..."
                                    )

                            except Exception as send_error:
                                logger.warning(
                                    f"Failed to send response for {session_id}: {send_error}"
                                )
                                session_data["is_running"] = False
                                break

                    except asyncio.TimeoutError:
                        # No response within timeout, continue listening
                        await asyncio.sleep(0.1)
                        continue

                except asyncio.CancelledError:
                    logger.info(f"Response handler cancelled for {session_id}")
                    break
                except Exception as e:
                    # Only log non-connection errors as warnings
                    if "connection" not in str(e).lower():
                        logger.warning(f"Response handling error for {session_id}: {e}")
                    # Add a small delay to prevent tight error loops
                    await asyncio.sleep(0.5)

        except Exception as e:
            logger.error(f"Response handler failed for {session_id}: {e}")
        finally:
            logger.info(f"Response handler ended for {session_id}")

    def _is_websocket_connected(self, websocket: WebSocket) -> bool:
        """Check if WebSocket is still connected."""
        if hasattr(websocket, "client_state"):
            return websocket.client_state.name == "CONNECTED"
        elif hasattr(websocket, "state"):
            return websocket.state == 1  # 1 = OPEN
        else:
            # Assume connected if we can't determine state
            return True

    def _get_timestamp(self):
        """Get current timestamp."""
        from datetime import datetime

        return datetime.now().isoformat()


# Global service instance
voice_agent = WebSocketVoiceAgent()

# Legacy compatibility
VoiceAgentService = WebSocketVoiceAgent
voice_agent_service = voice_agent
