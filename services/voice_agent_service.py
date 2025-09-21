"""
PyAudio-Free Voice Agent Service with Proper Gemini Live API Integration
Handles client-side audio via WebSocket streaming with correct protocol
"""

import os
import asyncio
import base64
import json
from typing import Dict, Any
from loguru import logger
from fastapi import WebSocket, WebSocketDisconnect

from google import genai
from google.genai import types

from datetime import datetime

# Audio configuration constants
SEND_SAMPLE_RATE = 16000
RECEIVE_SAMPLE_RATE = 24000
CHANNELS = 1
CHUNK_DURATION_MS = 100  # Send audio in 100ms chunks

# Compatibility for modality enums across SDK versions
try:
    MOD_TEXT = types.Modality.TEXT  # Preferred enum
    MOD_AUDIO = types.Modality.AUDIO
except Exception:
    MOD_TEXT = "TEXT"  # Fallback strings if enum unavailable
    MOD_AUDIO = "AUDIO"


# Initialize Gemini client with proper configuration
def get_gemini_client():
    """Get properly configured Gemini client."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set")

    # Ensure Google AI Studio endpoint (not Vertex) and avoid ambient ADC
    os.environ.pop("GOOGLE_GENAI_USE_VERTEXAI", None)
    os.environ.pop("GOOGLE_APPLICATION_CREDENTIALS", None)
    os.environ.pop("GCLOUD_PROJECT", None)

    # Select v1beta for Live API
    return genai.Client(api_key=api_key, http_options={"api_version": "v1beta"})


def build_persona_live_config() -> types.LiveConnectConfig:
    """Primary AUDIO config with system_instruction so persona is applied at setup."""
    return types.LiveConnectConfig(
        response_modalities=[MOD_AUDIO],
        speech_config=types.SpeechConfig(language_code="en-US"),
        generation_config=types.GenerationConfig(
            temperature=0.6,
            top_p=0.9,
        ),
        system_instruction=types.Content(
            parts=[
                types.Part.from_text(
                    text=(
                        "You are a compassionate mindfulness coach and mental wellness assistant. "
                        "IMPORTANT: You MUST speak ONLY in English. Do not use any other language under any circumstances. "
                        "Provide calming guidance, emotional support, and helpful meditation techniques. "
                        "Speak in a gentle, warm, and understanding tone. "
                        "Offer breathing exercises, meditation guidance, and positive affirmations when appropriate. "
                        "Keep responses conversational and natural."
                    )
                )
            ],
        ),
    )


def build_audio_fallback_config() -> types.LiveConnectConfig:
    """Plain AUDIO fallback if persona config is rejected by preview models."""
    return types.LiveConnectConfig(
        response_modalities=[MOD_AUDIO],
        speech_config=types.SpeechConfig(language_code="en-US"),
    )


class WebSocketVoiceAgent:
    """Voice Agent using WebSocket streaming with proper Gemini Live API protocol."""

    def __init__(self):
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.client = None

    def _ensure_client(self):
        """Ensure Gemini client is initialized."""
        if not self.client:
            self.client = get_gemini_client()

    async def create_session(self, session_id: str, websocket: WebSocket):
        """Create a new voice session with WebSocket connection."""
        try:
            logger.info(f"🎤 Creating voice session: {session_id}")
            self._ensure_client()

            logger.info("🤖 Connecting to Gemini Live API...")
            preferred_model = "gemini-2.0-flash-live-001"

            # Try multiple models
            models_to_try = [
                preferred_model,
                "gemini-live-2.5-flash-preview",
                "gemini-2.5-flash-preview-native-audio-dialog",
            ]
            seen = set()
            models_to_try = [m for m in models_to_try if not (m in seen or seen.add(m))]

            # IMPORTANT: persona config first so system_instruction is applied at setup
            configs_to_try = [
                ("persona-audio", build_persona_live_config()),
                ("audio-only-fallback", build_audio_fallback_config()),
                ("text-only", types.LiveConnectConfig(response_modalities=[MOD_TEXT])),
                ("bare", None),
            ]

            live_session = None
            successful_config = None

            for model_name in models_to_try:
                for config_name, config in configs_to_try:
                    try:
                        logger.info(
                            f"Trying model '{model_name}' with {config_name} configuration..."
                        )
                        if config is None:
                            live_session_context = self.client.aio.live.connect(
                                model=model_name
                            )
                        else:
                            live_session_context = self.client.aio.live.connect(
                                model=model_name, config=config
                            )

                        live_session = await live_session_context.__aenter__()
                        logger.info(
                            f"✅ Connected to {model_name} with {config_name} configuration!"
                        )
                        successful_config = config_name
                        preferred_model = model_name
                        raise StopIteration  # break out of both loops
                    except StopIteration:
                        break
                    except Exception as e:
                        logger.warning(
                            f"{config_name} config failed on {model_name}: {e}"
                        )
                        # Best-effort close on failure
                        if "live_session_context" in locals():
                            try:
                                await live_session_context.__aexit__(None, None, None)
                            except Exception:
                                pass
                        continue
                else:
                    continue
                break

            if not live_session:
                raise Exception("All configuration attempts failed")

            # Store session; arm immediately so client can stream mic
            self.active_sessions[session_id] = {
                "live_session": live_session,
                "live_session_context": live_session_context,
                "websocket": websocket,
                "is_running": True,
                "live_ready": True,
                "audio_buffer": bytearray(),
                "last_send_time": asyncio.get_event_loop().time(),
                "allow_audio": successful_config
                in ["persona-audio", "audio-only-fallback", "bare"],
                "config_used": successful_config,
            }

            # Notify client
            await websocket.send_text(
                json.dumps(
                    {
                        "type": "session_status",
                        "session_id": session_id,
                        "status": "connected",
                        "message": f"Voice session ready ({successful_config} config)",
                        "model": preferred_model,
                        "audio_enabled": True,
                        "timestamp": self._get_timestamp(),
                    }
                )
            )
            await websocket.send_text(
                json.dumps(
                    {
                        "type": "setup_complete",
                        "session_id": session_id,
                        "timestamp": self._get_timestamp(),
                    }
                )
            )

            # Run session loops
            await self._run_session(session_id)
            return True
        except Exception as e:
            logger.error(f"❌ Failed to create session {session_id}: {e}")
            try:
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "error",
                            "message": f"Failed to create session: {str(e)}",
                            "timestamp": self._get_timestamp(),
                        }
                    )
                )
            except:
                pass
            return False

    async def _run_session(self, session_id: str):
        """Run main session with proper cancellation on disconnect."""
        session_data = self.active_sessions.get(session_id)
        if not session_data:
            return

        receive_task = response_task = None
        try:
            receive_task = asyncio.create_task(self._handle_client_messages(session_id))
            response_task = asyncio.create_task(
                self._handle_model_responses(session_id)
            )

            done, pending = await asyncio.wait(
                {receive_task, response_task}, return_when=asyncio.FIRST_EXCEPTION
            )

            for t in done:
                exc = t.exception()
                if exc:
                    raise exc
        except Exception as e:
            logger.error(f"Session error for {session_id}: {e}")
        finally:
            for t in (receive_task, response_task):
                if t and not t.done():
                    t.cancel()
                    try:
                        await t
                    except asyncio.CancelledError:
                        pass

            sd = self.active_sessions.get(session_id)
            if sd:
                sd["is_running"] = False

            try:
                if sd and "live_session_context" in sd:
                    await sd["live_session_context"].__aexit__(None, None, None)
            except Exception as e:
                logger.warning(f"Error closing live session context: {e}")

            if session_id in self.active_sessions:
                del self.active_sessions[session_id]

    async def _handle_client_messages(self, session_id: str):
        """Handle incoming messages from the client; break on disconnect."""
        session_data = self.active_sessions.get(session_id)
        if not session_data:
            return

        websocket = session_data["websocket"]
        live_session = session_data["live_session"]

        try:
            while session_data.get("is_running", False):
                try:
                    message = await asyncio.wait_for(websocket.receive(), timeout=1.0)

                    if "text" in message:
                        data = json.loads(message["text"])
                        if data.get("type") == "text_message":
                            text = data.get("message", "")
                            logger.info(f"📝 Sending text: {text}")
                            await live_session.send_client_content(
                                turns=[
                                    types.Content(
                                        role="user",
                                        parts=[types.Part.from_text(text=text)],
                                    )
                                ],
                                turn_complete=True,
                            )
                            await websocket.send_text(
                                json.dumps(
                                    {
                                        "type": "message_sent",
                                        "session_id": session_id,
                                        "timestamp": self._get_timestamp(),
                                    }
                                )
                            )

                        elif data.get("type") == "end_turn":
                            logger.info("🔚 Ending turn")
                            # No explicit action; text path sets turn_complete

                    elif "bytes" in message:
                        if not session_data.get("allow_audio", True):
                            await websocket.send_text(
                                json.dumps(
                                    {
                                        "type": "error",
                                        "message": "Audio input disabled for this session configuration.",
                                        "timestamp": self._get_timestamp(),
                                    }
                                )
                            )
                            continue

                        if not session_data.get("live_ready", False):
                            session_data["audio_buffer"] = bytearray()
                            continue

                        audio_bytes = message["bytes"]
                        session_data["audio_buffer"].extend(audio_bytes)

                        samples_per_chunk = int(
                            SEND_SAMPLE_RATE * CHUNK_DURATION_MS / 1000
                        )
                        bytes_per_sample = 2  # int16 PCM
                        chunk_size = samples_per_chunk * bytes_per_sample

                        while len(session_data["audio_buffer"]) >= chunk_size:
                            chunk = bytes(session_data["audio_buffer"][:chunk_size])
                            del session_data["audio_buffer"][:chunk_size]

                            try:
                                await live_session.send_realtime_input(
                                    audio=types.Blob(
                                        data=chunk,
                                        mime_type=f"audio/pcm;rate={SEND_SAMPLE_RATE}",
                                    )
                                )
                            except Exception as audio_error:
                                logger.warning(f"Audio send error: {audio_error}")

                except asyncio.TimeoutError:
                    continue
                except WebSocketDisconnect:
                    logger.info(f"Client disconnected: {session_id}")
                    break
                except Exception as e:
                    logger.error(f"Error handling client messages: {e}")
                    break
        finally:
            sd = self.active_sessions.get(session_id)
            if sd:
                sd["is_running"] = False

    async def _handle_model_responses(self, session_id: str):
        """Handle responses from the model."""
        session_data = self.active_sessions.get(session_id)
        if not session_data:
            return

        live_session = session_data["live_session"]
        websocket = session_data["websocket"]

        try:
            while session_data["is_running"]:
                try:
                    async for response in live_session.receive():
                        if not session_data["is_running"]:
                            break

                        # Single audio stream: use inline_data within server_content parts
                        if (
                            hasattr(response, "server_content")
                            and response.server_content
                        ):
                            server_content = response.server_content

                            if getattr(server_content, "model_turn", None):
                                for part in server_content.model_turn.parts:
                                    if getattr(part, "text", None):
                                        await websocket.send_text(
                                            json.dumps(
                                                {
                                                    "type": "ai_response",
                                                    "session_id": session_id,
                                                    "text": part.text,
                                                    "timestamp": self._get_timestamp(),
                                                }
                                            )
                                        )

                                    if getattr(part, "inline_data", None):
                                        audio_b64 = base64.b64encode(
                                            part.inline_data.data
                                        ).decode("utf-8")
                                        await websocket.send_text(
                                            json.dumps(
                                                {
                                                    "type": "audio_response",
                                                    "session_id": session_id,
                                                    "audio_data": audio_b64,
                                                    "mime_type": part.inline_data.mime_type,
                                                    "timestamp": self._get_timestamp(),
                                                }
                                            )
                                        )

                            if getattr(server_content, "turn_complete", None):
                                await websocket.send_text(
                                    json.dumps(
                                        {
                                            "type": "turn_complete",
                                            "session_id": session_id,
                                            "timestamp": self._get_timestamp(),
                                        }
                                    )
                                )

                        # Idempotent setup_complete if surfaced by SDK
                        if getattr(response, "setup_complete", None) or getattr(
                            response, "setupComplete", None
                        ):
                            sd = self.active_sessions.get(session_id)
                            if sd:
                                sd["live_ready"] = True
                            await websocket.send_text(
                                json.dumps(
                                    {
                                        "type": "setup_complete",
                                        "session_id": session_id,
                                        "timestamp": self._get_timestamp(),
                                    }
                                )
                            )

                except asyncio.TimeoutError:
                    await asyncio.sleep(0.1)
                    continue
                except Exception as e:
                    logger.error(f"Error handling model responses: {e}")
                    break
        except Exception as e:
            logger.error(f"Model response handler error: {e}")

    async def stop_session(self, session_id: str):
        """Stop a voice session."""
        if session_id not in self.active_sessions:
            return

        session_data = self.active_sessions[session_id]
        session_data["is_running"] = False

        try:
            if "live_session_context" in session_data:
                await session_data["live_session_context"].__aexit__(None, None, None)
        except Exception as e:
            logger.warning(f"Error closing live session: {e}")

        del self.active_sessions[session_id]
        logger.success(f"Session stopped: {session_id}")

    def _get_timestamp(self):
        """Get current timestamp."""
        return datetime.now().isoformat()


# Enhanced WebSocket Voice Agent with model selection
class EnhancedWebSocketVoiceAgent(WebSocketVoiceAgent):
    """Enhanced version with model selection capability."""

    AVAILABLE_MODELS = [
        "gemini-2.0-flash-live-001",
        "gemini-live-2.5-flash-preview",
        "gemini-2.5-flash-preview-native-audio-dialog",
    ]

    def __init__(self, preferred_model: str = "gemini-2.0-flash-live-001"):
        super().__init__()
        self.preferred_model = (
            preferred_model
            if preferred_model in self.AVAILABLE_MODELS
            else self.AVAILABLE_MODELS[0]
        )

    async def create_session_with_model(
        self, session_id: str, websocket: WebSocket, model_name: str = None
    ):
        """Create session with specific model."""
        if model_name and model_name in self.AVAILABLE_MODELS:
            self.preferred_model = model_name
        return await self.create_session(session_id, websocket)


# Global service instances
voice_agent = WebSocketVoiceAgent()
enhanced_voice_agent = EnhancedWebSocketVoiceAgent()


# Legacy compatibility
class VoiceAgentService(WebSocketVoiceAgent):
    """Legacy compatibility wrapper."""

    pass


voice_agent_service = voice_agent
