"""
Voice Agent Router for Anime Generation
Provides REST endpoints for voice interaction and transcription
"""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Depends
from fastapi.responses import JSONResponse
from typing import Dict, Any, List, Optional
from loguru import logger
from datetime import datetime
import asyncio
import json
import os

from models.schemas import BaseModel
from services.voice_agent_service import voice_agent_service, voice_agent
from sqlalchemy.orm import Session
from models.db import get_db
from utils.auth import get_current_user, decode_token
from models.user import User
from models.voice import VoiceSession as DBVoiceSession, VoiceMessage as DBVoiceMessage
from utils.helpers import create_timestamp, log_api_call

# Create router instance
router = APIRouter()

# Active voice sessions tracking
active_sessions: Dict[str, Dict[str, Any]] = {}


class VoiceSessionRequest(BaseModel):
    """Request model for starting a voice session."""

    session_id: Optional[str] = None
    user_id: Optional[str] = None
    context: Optional[str] = "anime_generation"


class VoiceSessionResponse(BaseModel):
    """Response model for voice session operations."""

    session_id: str
    status: str
    message: str
    timestamp: str


class TextMessageRequest(BaseModel):
    """Request model for sending text messages to voice agent."""

    session_id: str
    message: str


class TranscriptionResponse(BaseModel):
    """Response model for transcription results."""

    session_id: str
    transcription: str
    timestamp: str
    confidence: Optional[float] = None


@router.post("/voice/start-session", response_model=VoiceSessionResponse)
async def start_voice_session(
    request: VoiceSessionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> VoiceSessionResponse:
    """
    Start a new voice agent session for anime generation assistance.

    This endpoint initializes a voice agent session that can:
    - Listen to user voice input
    - Provide voice responses about anime/manga creation
    - Assist with story development and character creation
    - Offer creative suggestions and feedback
    """
    try:
        session_id = (
            request.session_id
            or f"voice_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )

        logger.info(f"🎤 Starting voice session: {session_id}")
        log_api_call("/voice/start-session", request.dict())

        # Check if session already exists
        if session_id in active_sessions:
            raise HTTPException(
                status_code=400, detail=f"Voice session {session_id} already active"
            )

        # Create session callbacks
        async def transcription_callback(text: str):
            """Handle transcription results."""
            logger.info(f"📝 Transcription [{session_id}]: {text}")
            # Store transcription in session data
            if session_id in active_sessions:
                active_sessions[session_id]["last_transcription"] = {
                    "text": text,
                    "timestamp": create_timestamp(),
                }

            # Persist as user message
            try:
                db_sess = (
                    db.query(DBVoiceSession)
                    .filter(DBVoiceSession.session_id == session_id)
                    .first()
                )
                if db_sess:
                    msg = DBVoiceMessage(session_id=db_sess.id, role="user", text=text)
                    db.add(msg)
                    db.commit()
            except Exception as e:
                logger.warning(f"Failed to persist transcription for {session_id}: {e}")

        async def response_callback(text: str):
            """Handle AI responses."""
            logger.info(f"🤖 AI Response [{session_id}]: {text}")
            # Store response in session data
            if session_id in active_sessions:
                active_sessions[session_id]["last_response"] = {
                    "text": text,
                    "timestamp": create_timestamp(),
                }

            # Persist as ai message
            try:
                db_sess = (
                    db.query(DBVoiceSession)
                    .filter(DBVoiceSession.session_id == session_id)
                    .first()
                )
                if db_sess:
                    msg = DBVoiceMessage(session_id=db_sess.id, role="ai", text=text)
                    db.add(msg)
                    db.commit()
            except Exception as e:
                logger.warning(f"Failed to persist AI response for {session_id}: {e}")

        # Start voice agent session
        success = await voice_agent_service.start_session(
            session_id=session_id,
            transcription_callback=transcription_callback,
            response_callback=response_callback,
        )

        if not success:
            raise HTTPException(
                status_code=500, detail="Failed to initialize voice agent session"
            )

        # Track active session
        active_sessions[session_id] = {
            "user_id": str(current_user.id) if current_user else None,
            "context": request.context,
            "started_at": create_timestamp(),
            "status": "active",
            "last_transcription": None,
            "last_response": None,
        }

        # Persist DB voice session (auth optional; use provided user_id if available)
        try:
            # Attempt to coerce request.user_id to int if provided
            db_user_id = None
            if getattr(request, "user_id", None):
                try:
                    db_user_id = int(str(request.user_id))
                except Exception:
                    db_user_id = None

            db_session = DBVoiceSession(
                session_id=session_id,
                user_id=db_user_id or (current_user.id if current_user else None),
                context=request.context,
                status="active",
            )
            db.add(db_session)
            db.commit()
        except Exception as e:
            logger.warning(f"Failed to persist voice session {session_id}: {e}")

        response = VoiceSessionResponse(
            session_id=session_id,
            status="active",
            message="Voice agent session started successfully",
            timestamp=create_timestamp(),
        )

        logger.success(f"✅ Voice session started: {session_id}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to start voice session: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to start voice session: {str(e)}"
        )


@router.post("/voice/stop-session", response_model=VoiceSessionResponse)
async def stop_voice_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> VoiceSessionResponse:
    """
    Stop an active voice agent session.

    Args:
        session_id: The ID of the session to stop
    """
    try:
        logger.info(f"🛑 Stopping voice session: {session_id}")

        session_tracked = session_id in active_sessions
        service_tracked = session_id in voice_agent_service.active_sessions

        if not session_tracked and not service_tracked:
            # Nothing to stop
            raise HTTPException(
                status_code=404, detail=f"Voice session {session_id} not found"
            )

        # Stop the voice agent service regardless of router tracking state
        try:
            await voice_agent_service.stop_session(session_id)
        except Exception as e:
            logger.warning(f"Error stopping voice session in service: {e}")

        # Update session status
        if session_id in active_sessions:
            active_sessions[session_id]["status"] = "stopped"
            active_sessions[session_id]["stopped_at"] = create_timestamp()

        # Persist DB status update
        try:
            db_sess = (
                db.query(DBVoiceSession)
                .filter(DBVoiceSession.session_id == session_id)
                .first()
            )
            if db_sess:
                db_sess.status = "stopped"
                db_sess.stopped_at = datetime.utcnow()
                db.commit()
        except Exception as e:
            logger.warning(f"Failed to update DB voice session {session_id}: {e}")

        response = VoiceSessionResponse(
            session_id=session_id,
            status="stopped",
            message="Voice agent session stopped successfully",
            timestamp=create_timestamp(),
        )

        logger.success(f"✅ Voice session stopped: {session_id}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to stop voice session: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to stop voice session: {str(e)}"
        )


@router.post("/voice/send-message", response_model=Dict[str, Any])
async def send_text_message(
    request: TextMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Send a text message to the active voice agent.

    This can be used to:
    - Send text input when voice input is not available
    - Provide context or specific instructions
    - Ask specific questions about anime/manga creation
    """
    try:
        logger.info(f"📝 Sending text message to session: {request.session_id}")

        if request.session_id not in active_sessions:
            raise HTTPException(
                status_code=404, detail=f"Voice session {request.session_id} not found"
            )

        if active_sessions[request.session_id]["status"] != "active":
            raise HTTPException(
                status_code=400,
                detail=f"Voice session {request.session_id} is not active",
            )

        # Send message to voice agent
        success = await voice_agent_service.send_text_message(
            request.session_id, request.message
        )

        if not success:
            raise HTTPException(
                status_code=500, detail="Failed to send message to voice agent"
            )

        # Update session with sent message
        active_sessions[request.session_id]["last_sent_message"] = {
            "text": request.message,
            "timestamp": create_timestamp(),
        }

        # Persist user message
        try:
            db_sess = (
                db.query(DBVoiceSession)
                .filter(DBVoiceSession.session_id == request.session_id)
                .first()
            )
            if db_sess:
                msg = DBVoiceMessage(
                    session_id=db_sess.id, role="user", text=request.message
                )
                db.add(msg)
                db.commit()
        except Exception as e:
            logger.warning(
                f"Failed to persist text message for {request.session_id}: {e}"
            )

        return {
            "session_id": request.session_id,
            "status": "sent",
            "message": "Text message sent to voice agent",
            "sent_text": request.message,
            "timestamp": create_timestamp(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to send text message: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to send text message: {str(e)}"
        )


@router.get("/voice/session/{session_id}/status")
async def get_session_status(session_id: str) -> Dict[str, Any]:
    """
    Get the status and latest activity of a voice session.

    Returns:
    - Session status (active/stopped)
    - Latest transcription
    - Latest AI response
    - Session metadata
    """
    try:
        if session_id not in active_sessions:
            raise HTTPException(
                status_code=404, detail=f"Voice session {session_id} not found"
            )

        session_data = active_sessions[session_id]

        return {
            "session_id": session_id,
            "status": session_data["status"],
            "user_id": session_data.get("user_id"),
            "context": session_data.get("context"),
            "started_at": session_data["started_at"],
            "stopped_at": session_data.get("stopped_at"),
            "last_transcription": session_data.get("last_transcription"),
            "last_response": session_data.get("last_response"),
            "last_sent_message": session_data.get("last_sent_message"),
            "timestamp": create_timestamp(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get session status: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get session status: {str(e)}"
        )


@router.get("/voice/sessions")
async def list_active_sessions() -> Dict[str, Any]:
    """
    List all active voice sessions.

    Returns a summary of all currently active voice agent sessions.
    """
    try:
        sessions_summary = []

        for session_id, session_data in active_sessions.items():
            sessions_summary.append(
                {
                    "session_id": session_id,
                    "status": session_data["status"],
                    "user_id": session_data.get("user_id"),
                    "context": session_data.get("context"),
                    "started_at": session_data["started_at"],
                    "has_transcription": session_data.get("last_transcription")
                    is not None,
                    "has_response": session_data.get("last_response") is not None,
                }
            )

        return {
            "total_sessions": len(active_sessions),
            "active_sessions": len(
                [s for s in active_sessions.values() if s["status"] == "active"]
            ),
            "sessions": sessions_summary,
            "timestamp": create_timestamp(),
        }

    except Exception as e:
        logger.error(f"❌ Failed to list sessions: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to list sessions: {str(e)}"
        )


@router.get("/voice")
async def voice_agent_info() -> Dict[str, Any]:
    """
    Voice agent service information and available endpoints.
    """
    return {
        "service": "Voice Agent for Anime Generation",
        "version": "1.0.0",
        "description": "AI-powered voice assistant for anime and manga creation",
        "features": [
            "Real-time voice interaction with Gemini 2.5 Flash",
            "Voice transcription and text-to-speech",
            "Anime/manga creation assistance",
            "Creative brainstorming and feedback",
            "WebSocket real-time updates",
            "Session management and tracking",
        ],
        "endpoints": {
            "start_session": "/voice/start-session",
            "stop_session": "/voice/stop-session",
            "send_message": "/voice/send-message",
            "session_status": "/voice/session/{session_id}/status",
            "list_sessions": "/voice/sessions",
            "websocket": "/voice/ws/{session_id}",
            "health": "/voice/health",
        },
        "audio_config": {
            "input_sample_rate": 16000,
            "output_sample_rate": 24000,
            "channels": 1,
            "format": "16-bit PCM",
        },
        "model": "gemini-2.5-flash-live-preview",
        "timestamp": create_timestamp(),
    }


# New PyAudio-free WebSocket endpoint for client-side audio processing
@router.websocket("/voice/ws/{session_id}")
async def voice_websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time voice communication."""
    logger.info(f"🔌 WebSocket endpoint called for session: {session_id}")

    try:
        await websocket.accept()
        logger.info(f"✅ WebSocket connection accepted for session: {session_id}")
    except Exception as e:
        logger.error(f"❌ Failed to accept WebSocket connection for {session_id}: {e}")
        return

    # Track connection state
    is_connected = True

    try:
        # Create voice session
        logger.info(f"🎤 Attempting to create voice session: {session_id}")
        success = await voice_agent.create_session(session_id, websocket)
        logger.info(f"🔍 Session creation result for {session_id}: {success}")

        if not success:
            error_msg = (
                "Failed to create voice session - check Gemini API key and connection"
            )
            logger.error(f"❌ {error_msg} for session: {session_id}")
            try:
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "error",
                            "message": error_msg,
                            "timestamp": voice_agent._get_timestamp(),
                        }
                    )
                )
            except Exception:
                pass  # WebSocket might already be closed
            return

        logger.info(f"✅ Voice session created successfully: {session_id}")

        # Send connection confirmation
        try:
            await websocket.send_text(
                json.dumps(
                    {
                        "type": "session_status",
                        "session_id": session_id,
                        "status": "connected",
                        "message": "Voice session ready",
                        "timestamp": voice_agent._get_timestamp(),
                    }
                )
            )
            logger.info(f"📤 Sent connection confirmation for session: {session_id}")
        except Exception as e:
            logger.warning(f"Failed to send connection confirmation: {e}")
            is_connected = False

        # Handle incoming messages
        while is_connected:
            try:
                logger.debug(f"🔄 Waiting for messages from session: {session_id}")

                # Use a timeout to periodically check connection state
                data = await asyncio.wait_for(websocket.receive(), timeout=1.0)
                logger.debug(f"📥 Received data for session {session_id}: {type(data)}")

                if "text" in data:
                    # Handle text message
                    try:
                        message_data = json.loads(data["text"])
                        logger.info(
                            f"📝 Text message for {session_id}: {message_data.get('type', 'unknown')}"
                        )

                        if message_data.get("type") == "text_message":
                            success = await voice_agent.handle_text_message(
                                session_id, message_data.get("message", "")
                            )

                            if success and is_connected:
                                try:
                                    await websocket.send_text(
                                        json.dumps(
                                            {
                                                "type": "message_sent",
                                                "session_id": session_id,
                                                "status": "sent",
                                                "timestamp": voice_agent._get_timestamp(),
                                            }
                                        )
                                    )
                                except Exception:
                                    is_connected = False
                                    break
                        elif message_data.get("type") == "end_turn":
                            success = await voice_agent.end_turn(session_id)
                            if success and is_connected:
                                try:
                                    await websocket.send_text(
                                        json.dumps(
                                            {
                                                "type": "turn_ended",
                                                "session_id": session_id,
                                                "timestamp": voice_agent._get_timestamp(),
                                            }
                                        )
                                    )
                                except Exception:
                                    is_connected = False
                                    break
                    except json.JSONDecodeError as e:
                        logger.warning(
                            f"Invalid JSON in text message for {session_id}: {e}"
                        )

                elif "bytes" in data:
                    # Handle binary audio data
                    audio_data = data["bytes"]
                    logger.debug(
                        f"🎵 Audio data for {session_id}: {len(audio_data)} bytes"
                    )
                    await voice_agent.handle_audio_data(session_id, audio_data)

            except asyncio.TimeoutError:
                # Timeout is expected, continue the loop
                continue
            except WebSocketDisconnect:
                logger.info(f"🔌 Client disconnected from session: {session_id}")
                is_connected = False
                break
            except Exception as e:
                logger.error(f"❌ WebSocket message error for {session_id}: {e}")
                # Try to send error message if connection is still alive
                if is_connected:
                    try:
                        await websocket.send_text(
                            json.dumps(
                                {
                                    "type": "error",
                                    "message": f"Message handling error: {str(e)}",
                                    "timestamp": voice_agent._get_timestamp(),
                                }
                            )
                        )
                    except Exception:
                        # WebSocket is probably closed
                        is_connected = False
                        break

    except WebSocketDisconnect:
        logger.info(f"🔌 WebSocket disconnected during setup: {session_id}")
    except Exception as e:
        logger.error(f"❌ WebSocket endpoint error for {session_id}: {e}")
        logger.error(f"❌ Exception type: {type(e).__name__}")
        logger.error(f"❌ Exception details: {str(e)}")
    finally:
        logger.info(f"🧹 Cleaning up session: {session_id}")
        # Clean up session
        try:
            await voice_agent.stop_session(session_id)
            logger.info(f"✅ Session cleanup completed: {session_id}")
        except Exception as e:
            logger.warning(f"Error during session cleanup for {session_id}: {e}")


# Updated health check (no PyAudio dependencies)
@router.get("/voice/health")
async def voice_agent_health():
    """Health check for voice agent service."""
    try:
        health_status = {
            "service": "voice_agent",
            "status": "healthy",
            "timestamp": voice_agent._get_timestamp(),
            "checks": {},
        }

        # Check Gemini API key
        gemini_key = os.environ.get("GEMINI_API_KEY")
        health_status["checks"]["gemini_api_key"] = (
            "configured" if gemini_key else "missing"
        )

        # Audio processing now client-side
        health_status["checks"]["audio_system"] = "client-side (Web Audio API)"

        # Check active sessions
        active_count = len(voice_agent.active_sessions)
        health_status["checks"]["active_sessions"] = active_count

        if not gemini_key:
            health_status["status"] = "unhealthy"

        return health_status

    except Exception as e:
        return {
            "service": "voice_agent",
            "status": "unhealthy",
            "error": str(e),
            "timestamp": voice_agent._get_timestamp(),
        }
