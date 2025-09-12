"""
Voice Agent Service for Anime Generation
Provides voice interaction and transcription capabilities using Google Gemini Live API
"""

import os
import asyncio
import base64
import io
import traceback
import pyaudio
import numpy as np
from typing import Optional, Callable, Dict, Any
from loguru import logger
from google import genai
from google.genai import types

# Ensure we're using Google AI Studio, not Vertex AI
os.environ.pop("GOOGLE_GENAI_USE_VERTEXAI", None)

# Audio configuration
FORMAT = pyaudio.paInt16
CHANNELS = 1
SEND_SAMPLE_RATE = 16000
RECEIVE_SAMPLE_RATE = 24000
CHUNK_SIZE = 2048  # Increased chunk size for better audio stability

# Echo cancellation settings
ECHO_SUPPRESSION = True
VAD_THRESHOLD = 0.01  # Voice activity detection threshold
MODEL = "models/gemini-2.5-flash-live-preview"

# Initialize PyAudio
pya = pyaudio.PyAudio()

# Initialize Gemini client
client = genai.Client(
    http_options={"api_version": "v1beta"},
    api_key=os.environ.get("GEMINI_API_KEY"),
)

# Voice agent configuration for mindfulness coaching
VOICE_CONFIG = types.LiveConnectConfig(
    response_modalities=["AUDIO"],
    speech_config=types.SpeechConfig(
        language_code="en-US",
        voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Zephyr")
        ),
    ),
    system_instruction=types.Content(
        parts=[
            types.Part.from_text(
                text="""You are a compassionate mindfulness coach and mental wellness assistant. 
                IMPORTANT: You MUST speak ONLY in English. Do not use any other language under any circumstances.
                Your role is to provide calming guidance, emotional support, and helpful meditation techniques.
                Speak in a gentle, warm, and understanding tone. 
                Be empathetic and supportive while providing practical advice for managing stress, anxiety, and improving mental well-being.
                Offer breathing exercises, meditation guidance, and positive affirmations when appropriate.
                Keep responses conversational and natural."""
            )
        ],
        role="user",
    ),
)


class VoiceAgentService:
    """Voice Agent Service for anime generation assistance."""

    def __init__(self):
        self.session = None
        self.session_context = None
        self.audio_in_queue = None
        self.out_queue = None
        self.audio_stream = None
        self.is_running = False
        self.transcription_callback: Optional[Callable] = None
        self.response_callback: Optional[Callable] = None
        self.session_tasks: Dict[str, List[asyncio.Task]] = {}
        self.active_sessions: Dict[str, Dict[str, Any]] = {}

    async def start_session(
        self,
        session_id: str,
        transcription_callback: Optional[Callable] = None,
        response_callback: Optional[Callable] = None,
    ):
        """Start a voice agent session with session ID."""
        try:
            logger.info(f"🎤 Starting voice agent session: {session_id}")

            # Validate API key first
            api_key = os.environ.get("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY environment variable is not set")

            # Create session with Gemini Live API with timeout and retry
            session_context = client.aio.live.connect(
                model=MODEL, 
                config=VOICE_CONFIG
            )
            
            # Add connection timeout
            session = await asyncio.wait_for(
                session_context.__aenter__(), 
                timeout=15.0  # Reduced timeout
            )

            # Initialize queues for this session
            audio_in_queue = asyncio.Queue(maxsize=100)  # Increased queue size to prevent audio drops
            out_queue = asyncio.Queue(maxsize=50)  # Increased for better buffering

            # Store session data
            self.active_sessions[session_id] = {
                'session': session,
                'session_context': session_context,
                'audio_in_queue': audio_in_queue,
                'out_queue': out_queue,
                'audio_stream': None,
                'is_running': True,
                'transcription_callback': transcription_callback,
                'response_callback': response_callback
            }

            # Start session tasks
            await self._start_session_tasks(session_id)

            logger.success(f"✅ Voice agent session started: {session_id}")
            return True

        except asyncio.TimeoutError:
            logger.error(f"❌ Timeout starting voice agent session {session_id}")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to start voice agent session {session_id}: {e}")
            # Clean up any partial session data
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
            return False

    async def stop_session(self, session_id: str):
        """Stop a specific voice agent session."""
        try:
            logger.info(f"🛑 EMERGENCY STOP: Stopping voice agent session: {session_id}")

            if session_id not in self.active_sessions:
                logger.warning(f"Session {session_id} not found")
                return

            session_data = self.active_sessions[session_id]
            
            # IMMEDIATE STOP: Mark session as not running first
            session_data['is_running'] = False
            logger.info(f"🔄 Marked session {session_id} as not running")
            
            # IMMEDIATE: Clear audio queue to stop any pending audio
            if session_data.get('audio_in_queue'):
                try:
                    while not session_data['audio_in_queue'].empty():
                        try:
                            session_data['audio_in_queue'].get_nowait()
                        except:
                            break
                    logger.info(f"🔇 EMERGENCY: Audio queue cleared for {session_id}")
                except Exception as queue_error:
                    logger.warning(f"Error clearing audio queue: {queue_error}")
            
            # IMMEDIATE: Force close Gemini session to stop AI generation
            if session_data.get('session'):
                try:
                    # Force terminate the Gemini session
                    session_data['session'] = None
                    logger.info(f"🤖 EMERGENCY: Gemini session terminated for {session_id}")
                except Exception as gemini_error:
                    logger.warning(f"Error terminating Gemini session: {gemini_error}")

            # Cancel all session tasks
            if session_id in self.session_tasks:
                tasks = self.session_tasks[session_id]
                logger.info(f"🚫 Cancelling {len(tasks)} tasks for session {session_id}")
                
                for i, task in enumerate(tasks):
                    if not task.done():
                        task.cancel()
                        logger.debug(f"Cancelled task {i+1}/{len(tasks)}")
                
                # Wait for all tasks to complete cancellation
                await asyncio.gather(*tasks, return_exceptions=True)
                logger.info(f"✅ All tasks cancelled for session {session_id}")
                
                del self.session_tasks[session_id]

            # Close audio stream
            if session_data.get('audio_stream'):
                try:
                    session_data['audio_stream'].stop_stream()
                    session_data['audio_stream'].close()
                    logger.info(f"🎧 Audio stream closed for {session_id}")
                except Exception as audio_error:
                    logger.warning(f"Audio stream close error: {audio_error}")

            # Clear audio queue immediately to stop any pending audio
            if session_data.get('audio_in_queue'):
                try:
                    # Clear all pending audio from queue
                    while not session_data['audio_in_queue'].empty():
                        try:
                            session_data['audio_in_queue'].get_nowait()
                        except:
                            break
                    logger.info(f"🔇 Audio queue cleared for {session_id}")
                except Exception as queue_error:
                    logger.warning(f"Error clearing audio queue: {queue_error}")

            # Close Gemini session
            if session_data.get('session') and session_data.get('session_context'):
                try:
                    await session_data['session_context'].__aexit__(None, None, None)
                    logger.info(f"🤖 Gemini session closed for {session_id}")
                except Exception as session_error:
                    logger.warning(f"Session cleanup warning: {session_error}")

            # Remove session data
            del self.active_sessions[session_id]

            logger.success(f"✅ Voice agent session completely stopped: {session_id}")

        except Exception as e:
            logger.error(f"❌ Error stopping voice agent session {session_id}: {e}")
            # Force cleanup even if there are errors
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
            if session_id in self.session_tasks:
                del self.session_tasks[session_id]

    async def listen_audio(self):
        """Listen to microphone input and send to Gemini."""
        try:
            mic_info = pya.get_default_input_device_info()
            self.audio_stream = await asyncio.to_thread(
                pya.open,
                format=FORMAT,
                channels=CHANNELS,
                rate=SEND_SAMPLE_RATE,
                input=True,
                input_device_index=mic_info["index"],
                frames_per_buffer=CHUNK_SIZE,
            )

            logger.info("🎧 Audio listening started")

            kwargs = {"exception_on_overflow": False}

            while self.is_running:
                try:
                    data = await asyncio.to_thread(
                        self.audio_stream.read, CHUNK_SIZE, **kwargs
                    )
                    await self.out_queue.put({"data": data, "mime_type": "audio/pcm"})
                except Exception as e:
                    if self.is_running:
                        logger.warning(f"Audio read error: {e}")
                    break

        except Exception as e:
            logger.error(f"❌ Audio listening failed: {e}")

    async def send_realtime(self):
        """Send audio data to Gemini in real-time."""
        try:
            while self.is_running:
                try:
                    msg = await asyncio.wait_for(self.out_queue.get(), timeout=1.0)
                    if self.session:
                        await self.session.send(input=msg)
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    if self.is_running:
                        logger.warning(f"Send realtime error: {e}")
                    break

        except Exception as e:
            logger.error(f"❌ Send realtime failed: {e}")

    async def receive_audio(self):
        """Receive audio responses from Gemini."""
        try:
            while self.is_running:
                try:
                    if not self.session:
                        break

                    turn = self.session.receive()
                    async for response in turn:
                        if not self.is_running:
                            break

                        # Handle audio data
                        if data := response.data:
                            self.audio_in_queue.put_nowait(data)
                            continue

                        # Handle text transcription
                        if text := response.text:
                            logger.info(f"🤖 AI Response: {text}")
                            if self.response_callback:
                                await self.response_callback(text)

                        # Handle interruptions
                        if (
                            hasattr(response, "turn_complete")
                            and response.turn_complete
                        ):
                            # Clear audio queue on interruption
                            while not self.audio_in_queue.empty():
                                try:
                                    self.audio_in_queue.get_nowait()
                                except:
                                    break

                except Exception as e:
                    if self.is_running:
                        logger.warning(f"Receive audio error: {e}")
                    break

        except Exception as e:
            logger.error(f"❌ Receive audio failed: {e}")

    async def play_audio(self):
        """Play audio responses from Gemini."""
        try:
            stream = await asyncio.to_thread(
                pya.open,
                format=FORMAT,
                channels=CHANNELS,
                rate=RECEIVE_SAMPLE_RATE,
                output=True,
            )

            logger.info("🔊 Audio playback started")

            while self.is_running:
                try:
                    bytestream = await asyncio.wait_for(
                        self.audio_in_queue.get(), timeout=1.0
                    )
                    await asyncio.to_thread(stream.write, bytestream)
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    if self.is_running:
                        logger.warning(f"Audio playback error: {e}")
                    break

            stream.close()

        except Exception as e:
            logger.error(f"❌ Audio playback failed: {e}")

    async def send_text_message(self, session_id: str, message: str):
        """Send a text message to a specific voice agent session."""
        try:
            if session_id not in self.active_sessions:
                logger.error(f"Session {session_id} not found")
                return False
                
            session_data = self.active_sessions[session_id]
            session = session_data.get('session')
            
            if session and message.strip():
                await session.send(input=message, end_of_turn=True)
                logger.info(f"📝 Sent text message to {session_id}: {message}")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Failed to send text message to {session_id}: {e}")
            return False

    async def run_voice_session(
        self,
        transcription_callback: Optional[Callable] = None,
        response_callback: Optional[Callable] = None,
    ):
        """Run a complete voice agent session with all components."""
        try:
            # Start session
            if not await self.start_session(transcription_callback, response_callback):
                return False

            # Run all tasks concurrently
            async with asyncio.TaskGroup() as tg:
                tg.create_task(self.send_realtime())
                tg.create_task(self.listen_audio())
                tg.create_task(self.receive_audio())
                tg.create_task(self.play_audio())

                logger.success("🎤 Voice agent session running...")

        except asyncio.CancelledError:
            logger.info("Voice agent session cancelled")
        except Exception as e:
            logger.error(f"❌ Voice agent session failed: {e}")
            traceback.print_exc()
        finally:
            await self.stop_session()


    async def _start_session_tasks(self, session_id: str):
        """Start background tasks for a voice session."""
        try:
            # Create individual tasks for this session
            tasks = [
                asyncio.create_task(self._send_realtime(session_id)),
                asyncio.create_task(self._listen_audio(session_id)),
                asyncio.create_task(self._receive_audio(session_id)),
                asyncio.create_task(self._play_audio(session_id))
            ]
            
            # Store all tasks for this session
            self.session_tasks[session_id] = tasks
            logger.info(f"✅ Started {len(tasks)} tasks for session {session_id}")
            
        except Exception as e:
            logger.error(f"Failed to start session tasks for {session_id}: {e}")

    async def _send_realtime(self, session_id: str):
        """Send audio data to Gemini for a specific session."""
        session_data = self.active_sessions.get(session_id)
        if not session_data:
            return
            
        try:
            while session_data['is_running']:
                try:
                    msg = await asyncio.wait_for(session_data['out_queue'].get(), timeout=1.0)
                    if session_data['session'] and session_data['is_running']:
                        await session_data['session'].send(input=msg)
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    error_msg = str(e)
                    if session_data['is_running']:
                        logger.warning(f"Send realtime error for {session_id}: {e}")
                        # Check for fatal errors
                        if "1007" in error_msg or "1008" in error_msg or "invalid frame" in error_msg:
                            logger.error(f"🚨 Fatal send error for {session_id}: {error_msg}")
                            session_data['is_running'] = False
                    break
        except Exception as e:
            logger.error(f"Send realtime failed for {session_id}: {e}")
        finally:
            if session_data:
                session_data['is_running'] = False


    async def _listen_audio(self, session_id: str):
        """Listen to microphone input for a specific session."""
        session_data = self.active_sessions.get(session_id)
        if not session_data:
            return
            
        try:
            mic_info = pya.get_default_input_device_info()
            audio_stream = await asyncio.to_thread(
                pya.open,
                format=FORMAT,
                channels=CHANNELS,
                rate=SEND_SAMPLE_RATE,
                input=True,
                input_device_index=mic_info["index"],
                frames_per_buffer=CHUNK_SIZE,
            )
            session_data['audio_stream'] = audio_stream

            logger.info(f"🎧 Audio listening started for {session_id}")
            kwargs = {"exception_on_overflow": False}
            
            while session_data['is_running']:
                try:
                    data = await asyncio.to_thread(
                        audio_stream.read, CHUNK_SIZE, **kwargs
                    )
                    
                    await session_data['out_queue'].put({"data": data, "mime_type": "audio/pcm"})
                except Exception as e:
                    if session_data['is_running']:
                        logger.warning(f"Audio read error for {session_id}: {e}")
                    break

        except Exception as e:
            logger.error(f"Audio listening failed for {session_id}: {e}")

    async def _receive_audio(self, session_id: str):
        """Receive audio and text responses from Gemini for a specific session."""
        session_data = self.active_sessions.get(session_id)
        if not session_data:
            return
            
        try:
            while session_data['is_running']:
                # Check if session is still valid before processing
                if not session_data.get('session'):
                    logger.info(f"🛑 Gemini session terminated, stopping receive for {session_id}")
                    break
                    
                try:
                    turn = session_data['session'].receive()
                    async for response in turn:
                        # Double-check session is still running
                        if not session_data['is_running']:
                            logger.info(f"🛑 Session stopped during response processing for {session_id}")
                            break
                            
                            
                        # Handle audio data
                        if data := response.data:
                            # Check if session is still running FIRST
                            if not session_data['is_running']:
                                break  # Exit immediately if stopped
                            
                            # Only add audio if session is still running
                            if session_data['is_running']:
                                try:
                                    session_data['audio_in_queue'].put_nowait(data)
                                except asyncio.QueueFull:
                                    # Log but don't block - allows immediate stop
                                    logger.debug(f"Audio queue full for {session_id}, skipping chunk")
                            continue
                            
                        # Handle text transcription
                        if text := response.text:
                            logger.info(f"🤖 AI Response: {text}")
                            if session_data.get('response_callback') and session_data['is_running']:
                                await session_data['response_callback'](text)
                            continue
                            
                            
                except asyncio.TimeoutError:
                    continue
                except asyncio.CancelledError:
                    logger.info(f"🛑 Receive audio task cancelled for {session_id}")
                    break
                except Exception as e:
                    error_msg = str(e)
                    logger.warning(f"Receive audio error for {session_id}: {e}")
                    
                    # Check for fatal WebSocket errors
                    if "1007" in error_msg or "1008" in error_msg or "invalid frame" in error_msg or "policy violation" in error_msg:
                        logger.error(f"🚨 Fatal Gemini API error for {session_id}: {error_msg}")
                        session_data['is_running'] = False
                        break
                    
                    # For other errors, wait briefly and continue
                    await asyncio.sleep(0.1)
                    continue

        except asyncio.CancelledError:
            logger.info(f"🛑 Receive audio task cancelled for {session_id}")
        except Exception as e:
            logger.error(f"Receive audio failed for {session_id}: {e}")
        finally:
            # Ensure session is marked as not running if we exit the loop
            if session_data:
                session_data['is_running'] = False
                logger.info(f"🛑 Receive audio task ended for {session_id}")

    async def _play_audio(self, session_id: str):
        """Play audio responses for a specific session."""
        session_data = self.active_sessions.get(session_id)
        if not session_data:
            return
            
        stream = None
        try:
            stream = await asyncio.to_thread(
                pya.open,
                format=FORMAT,
                channels=CHANNELS,
                rate=RECEIVE_SAMPLE_RATE,
                output=True,
            )

            logger.info(f"🔊 Audio playback started for {session_id}")

            while session_data['is_running']:
                try:
                    # Use short timeout for immediate stop response
                    bytestream = await asyncio.wait_for(
                        session_data['audio_in_queue'].get(), timeout=0.5
                    )
                    # Double-check if session is still running before playing
                    if not session_data['is_running']:
                        logger.info(f"🛑 Audio playback stopped mid-stream for {session_id}")
                        break
                    
                    # Play audio chunk
                    await asyncio.to_thread(stream.write, bytestream)
                    
                except asyncio.TimeoutError:
                    continue
                except asyncio.CancelledError:
                    logger.info(f"🛑 Audio playback task cancelled for {session_id}")
                    break
                except Exception as e:
                    if session_data['is_running']:
                        logger.warning(f"Audio playback error for {session_id}: {e}")
                    break

        except asyncio.CancelledError:
            logger.info(f"🛑 Audio playback task cancelled during setup for {session_id}")
        except Exception as e:
            logger.error(f"Audio playback failed for {session_id}: {e}")
        finally:
            if stream:
                try:
                    stream.stop_stream()
                    stream.close()
                    logger.info(f"🔇 Audio stream closed for {session_id}")
                except Exception as close_error:
                    logger.warning(f"Error closing audio stream: {close_error}")


# Global voice agent service instance
voice_agent_service = VoiceAgentService()
