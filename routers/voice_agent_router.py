"""
Voice Agent Router for Anime Generation
Provides REST endpoints for voice interaction and transcription
"""

from fastapi import (
    APIRouter,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
    Depends,
    Query,
)
from fastapi.responses import JSONResponse
from typing import Dict, Any, List, Optional
from loguru import logger
from datetime import datetime
import asyncio
import json
import os

from models.schemas import BaseModel

# ✅ Updated imports to match new service
from services.voice_agent_service import (
    voice_agent,
    enhanced_voice_agent,
    EnhancedWebSocketVoiceAgent,
)
from sqlalchemy.orm import Session
from models.db import get_db
from utils.auth import get_current_user, decode_token
from models.user import User
from models.voice import VoiceSession as DBVoiceSession, VoiceMessage as DBVoiceMessage
from utils.helpers import create_timestamp, log_api_call

# Create router instance
router = APIRouter()

# Active voice sessions tracking (simplified - WebSocket handles the real sessions)
active_sessions: Dict[str, Dict[str, Any]] = {}


class VoiceSessionRequest(BaseModel):
    """Request model for starting a voice session."""

    session_id: Optional[str] = None
    user_id: Optional[str] = None
    context: Optional[str] = "anime_generation"
    model: Optional[str] = "gemini-2.0-flash-live-001"  # ✅ Updated default model
    system_instruction: Optional[str] = None  # Custom system instruction
    use_persona: Optional[bool] = True  # Whether to use persona config


class VoiceSessionResponse(BaseModel):
    """Response model for voice session operations."""

    session_id: str
    status: str
    message: str
    timestamp: str
    model: Optional[str] = None
    config_used: Optional[str] = None  # Which configuration was used


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
    Initialize a voice session (WebSocket connection required for actual functionality).

    This endpoint prepares the session metadata. The actual voice interaction
    happens through the WebSocket endpoint /voice/ws/{session_id}.
    """
    try:
        session_id = (
            request.session_id
            or f"voice_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )

        logger.info(f"🎤 Preparing voice session: {session_id}")
        log_api_call("/voice/start-session", request.dict())

        # Check if session already exists
        if session_id in active_sessions:
            raise HTTPException(
                status_code=400, detail=f"Voice session {session_id} already active"
            )

        # ✅ Updated: Store session metadata (actual session created via WebSocket)
        active_sessions[session_id] = {
            "user_id": str(current_user.id) if current_user else None,
            "context": request.context,
            "model": request.model,
            "started_at": create_timestamp(),
            "status": "initialized",  # Will become "connected" via WebSocket
            "websocket_connected": False,
        }

        # Persist DB voice session
        try:
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
                status="initialized",
            )
            db.add(db_session)
            db.commit()
        except Exception as e:
            logger.warning(f"Failed to persist voice session {session_id}: {e}")

        response = VoiceSessionResponse(
            session_id=session_id,
            status="initialized",
            message="Voice session prepared. Connect via WebSocket to /voice/ws/{session_id}",
            model=request.model,
            timestamp=create_timestamp(),
        )

        logger.success(f"✅ Voice session prepared: {session_id}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to prepare voice session: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to prepare voice session: {str(e)}"
        )


@router.post("/voice/stop-session", response_model=VoiceSessionResponse)
async def stop_voice_session(
    session_id: str = Query(..., description="The session ID to stop"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> VoiceSessionResponse:
    """Stop an active voice agent session."""
    try:
        logger.info(f"🛑 Stopping voice session: {session_id}")

        session_tracked = session_id in active_sessions
        websocket_tracked = session_id in voice_agent.active_sessions

        if not session_tracked and not websocket_tracked:
            raise HTTPException(
                status_code=404, detail=f"Voice session {session_id} not found"
            )

        # ✅ Stop the WebSocket voice session
        try:
            await voice_agent.stop_session(session_id)
        except Exception as e:
            logger.warning(f"Error stopping WebSocket voice session: {e}")

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
    Send a text message to the active voice agent via WebSocket.

    Note: This requires an active WebSocket connection to work.
    """
    try:
        logger.info(
            f"📝 Attempting to send text message to session: {request.session_id}"
        )

        if request.session_id not in active_sessions:
            raise HTTPException(
                status_code=404, detail=f"Voice session {request.session_id} not found"
            )

        if active_sessions[request.session_id]["status"] not in [
            "initialized",
            "connected",
        ]:
            raise HTTPException(
                status_code=400,
                detail=f"Voice session {request.session_id} is not active",
            )

        # ✅ Check if WebSocket session exists
        if request.session_id not in voice_agent.active_sessions:
            raise HTTPException(
                status_code=400,
                detail=f"WebSocket connection required for session {request.session_id}. Connect to /voice/ws/{request.session_id} first.",
            )

        # Update session with sent message (WebSocket handles actual sending)
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
            "status": "queued",
            "message": "Text message will be sent via active WebSocket connection",
            "sent_text": request.message,
            "timestamp": create_timestamp(),
            "note": "Message processing depends on active WebSocket connection",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to queue text message: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to queue text message: {str(e)}"
        )


@router.get("/voice/session/{session_id}/status")
async def get_session_status(session_id: str) -> Dict[str, Any]:
    """Get the status and latest activity of a voice session."""
    try:
        router_tracked = session_id in active_sessions
        websocket_tracked = session_id in voice_agent.active_sessions

        if not router_tracked and not websocket_tracked:
            raise HTTPException(
                status_code=404, detail=f"Voice session {session_id} not found"
            )

        # Combine router and WebSocket session data
        status_data = {
            "session_id": session_id,
            "router_status": active_sessions.get(session_id, {}).get(
                "status", "unknown"
            ),
            "websocket_connected": websocket_tracked,
            "timestamp": create_timestamp(),
        }

        # Add router session data if available
        if router_tracked:
            session_data = active_sessions[session_id]
            status_data.update(
                {
                    "user_id": session_data.get("user_id"),
                    "context": session_data.get("context"),
                    "model": session_data.get("model"),
                    "started_at": session_data["started_at"],
                    "stopped_at": session_data.get("stopped_at"),
                    "last_sent_message": session_data.get("last_sent_message"),
                }
            )

        # Add WebSocket session data if available
        if websocket_tracked:
            ws_session = voice_agent.active_sessions[session_id]
            status_data.update(
                {
                    "websocket_status": (
                        "connected" if ws_session["is_running"] else "disconnected"
                    ),
                    "websocket_buffer_size": len(ws_session.get("audio_buffer", [])),
                }
            )

        return status_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get session status: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get session status: {str(e)}"
        )


@router.get("/voice/sessions")
async def list_active_sessions() -> Dict[str, Any]:
    """List all active voice sessions."""
    try:
        sessions_summary = []

        # Combine router and WebSocket sessions
        all_session_ids = set(active_sessions.keys()) | set(
            voice_agent.active_sessions.keys()
        )

        for session_id in all_session_ids:
            router_data = active_sessions.get(session_id, {})
            websocket_data = voice_agent.active_sessions.get(session_id, {})

            sessions_summary.append(
                {
                    "session_id": session_id,
                    "router_status": router_data.get("status", "unknown"),
                    "websocket_connected": session_id in voice_agent.active_sessions,
                    "websocket_running": websocket_data.get("is_running", False),
                    "user_id": router_data.get("user_id"),
                    "context": router_data.get("context"),
                    "model": router_data.get("model"),
                    "started_at": router_data.get("started_at"),
                }
            )

        return {
            "total_sessions": len(all_session_ids),
            "router_sessions": len(active_sessions),
            "websocket_sessions": len(voice_agent.active_sessions),
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
    """Voice agent service information and available endpoints."""
    return {
        "service": "Voice Agent for Anime Generation",
        "version": "2.0.0",  # ✅ Updated version
        "description": "AI-powered voice assistant for anime and manga creation using Gemini Live API",
        "features": [
            "Real-time voice interaction with Gemini 2.0 Flash Live",
            "WebSocket-based audio streaming (PyAudio-free)",
            "Multiple model support",
            "Anime/manga creation assistance",
            "Creative brainstorming and feedback",
            "Session management and tracking",
        ],
        "available_models": [  # ✅ Added available models
            "gemini-2.0-flash-live-001",
            "gemini-live-2.5-flash-preview",
            "gemini-2.5-flash-preview-native-audio-dialog",
        ],
        "default_model": "gemini-2.0-flash-live-001",  # ✅ Updated default
        "endpoints": {
            "start_session": "/voice/start-session",
            "start_persona_session": "/voice/start-persona-session",
            "stop_session": "/voice/stop-session",
            "send_message": "/voice/send-message",
            "session_status": "/voice/session/{session_id}/status",
            "list_sessions": "/voice/sessions",
            "websocket": "/voice/ws/{session_id}",
            "persona_config": "/voice/persona/config",
            "update_persona_instruction": "/voice/persona/update-instruction",
            "session_persona_info": "/voice/persona/session/{session_id}",
            "health": "/voice/health",
        },
        "audio_config": {
            "input_sample_rate": 16000,
            "output_sample_rate": 24000,
            "channels": 1,
            "format": "16-bit PCM",
            "chunk_duration_ms": 100,
        },
        "timestamp": create_timestamp(),
    }


# ✅ NEW: Enhanced persona configuration routes
@router.post("/voice/start-persona-session", response_model=VoiceSessionResponse)
async def start_persona_voice_session(
    request: VoiceSessionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> VoiceSessionResponse:
    """
    Start a voice session with custom persona configuration.
    Allows custom system instructions and persona settings.
    """
    try:
        session_id = (
            request.session_id
            or f"persona_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )

        logger.info(f"🎭 Preparing persona voice session: {session_id}")
        log_api_call("/voice/start-persona-session", request.dict())

        # Check if session already exists
        if session_id in active_sessions:
            raise HTTPException(
                status_code=400, detail=f"Voice session {session_id} already active"
            )

        # Store persona configuration in session metadata
        active_sessions[session_id] = {
            "user_id": str(current_user.id) if current_user else None,
            "context": request.context,
            "model": request.model,
            "started_at": create_timestamp(),
            "status": "initialized",
            "websocket_connected": False,
            "system_instruction": request.system_instruction,
            "use_persona": request.use_persona,
            "session_type": "persona",
        }

        # Persist DB voice session with persona info
        try:
            db_user_id = None
            if getattr(request, "user_id", None):
                try:
                    db_user_id = int(str(request.user_id))
                except Exception:
                    db_user_id = None

            db_session = DBVoiceSession(
                session_id=session_id,
                user_id=db_user_id or (current_user.id if current_user else None),
                context=(
                    f"{request.context}_persona"
                    if request.use_persona
                    else request.context
                ),
                status="initialized",
            )
            db.add(db_session)
            db.commit()
        except Exception as e:
            logger.warning(f"Failed to persist persona voice session {session_id}: {e}")

        response = VoiceSessionResponse(
            session_id=session_id,
            status="initialized",
            message="Persona voice session prepared. Connect via WebSocket to /voice/ws/{session_id}",
            model=request.model,
            timestamp=create_timestamp(),
            config_used="persona" if request.use_persona else "standard",
        )

        logger.success(f"✅ Persona voice session prepared: {session_id}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to prepare persona voice session: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to prepare persona voice session: {str(e)}"
        )


@router.get("/voice/persona/config")
async def get_persona_config() -> Dict[str, Any]:
    """Get the current persona configuration options."""
    return {
        "default_persona": {
            "system_instruction": (
                "You are a compassionate mindfulness coach and mental wellness assistant. "
                "IMPORTANT: You MUST speak ONLY in English. Do not use any other language under any circumstances. "
                "Provide calming guidance, emotional support, and helpful meditation techniques. "
                "Speak in a gentle, warm, and understanding tone. "
                "Offer breathing exercises, meditation guidance, and positive affirmations when appropriate. "
                "Keep responses conversational and natural."
            ),
            "temperature": 0.6,
            "top_p": 0.9,
            "language_code": "en-US",
        },
        "available_configs": [
            {
                "name": "persona-audio",
                "description": "Full persona with system instructions and audio response",
                "modalities": ["audio"],
                "recommended": True,
            },
            {
                "name": "audio-only-fallback",
                "description": "Audio-only without persona for compatibility",
                "modalities": ["audio"],
                "recommended": False,
            },
            {
                "name": "text-only",
                "description": "Text responses only (fallback mode)",
                "modalities": ["text"],
                "recommended": False,
            },
        ],
        "supported_models": [
            "gemini-2.0-flash-live-001",
            "gemini-live-2.5-flash-preview",
            "gemini-2.5-flash-preview-native-audio-dialog",
        ],
        "timestamp": create_timestamp(),
    }


@router.post("/voice/persona/update-instruction")
async def update_persona_instruction(
    session_id: str,
    instruction: str,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Update the system instruction for an active voice session."""
    try:
        if session_id not in active_sessions:
            raise HTTPException(
                status_code=404, detail=f"Voice session {session_id} not found"
            )

        # Update the stored instruction
        active_sessions[session_id]["system_instruction"] = instruction
        active_sessions[session_id]["updated_at"] = create_timestamp()

        logger.info(f"🎭 Updated persona instruction for session: {session_id}")

        return {
            "session_id": session_id,
            "status": "updated",
            "message": "System instruction updated successfully",
            "new_instruction": instruction,
            "timestamp": create_timestamp(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to update persona instruction: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to update persona instruction: {str(e)}"
        )


@router.get("/voice/persona/session/{session_id}")
async def get_session_persona_info(
    session_id: str,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get persona configuration information for a specific session."""
    try:
        if session_id not in active_sessions:
            raise HTTPException(
                status_code=404, detail=f"Voice session {session_id} not found"
            )

        session_data = active_sessions[session_id]
        websocket_data = voice_agent.active_sessions.get(session_id, {})

        return {
            "session_id": session_id,
            "session_type": session_data.get("session_type", "standard"),
            "use_persona": session_data.get("use_persona", True),
            "system_instruction": session_data.get("system_instruction"),
            "context": session_data.get("context"),
            "model": session_data.get("model"),
            "config_used": websocket_data.get("config_used", "unknown"),
            "websocket_connected": session_id in voice_agent.active_sessions,
            "status": session_data.get("status"),
            "started_at": session_data.get("started_at"),
            "updated_at": session_data.get("updated_at"),
            "timestamp": create_timestamp(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get session persona info: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get session persona info: {str(e)}"
        )


# ✅ Updated WebSocket endpoint - now properly integrated
# In voice_agent_router.py, fix the WebSocket endpoint:


@router.websocket("/voice/ws/{session_id}")
async def voice_websocket_endpoint(
    websocket: WebSocket, session_id: str, db: Session = Depends(get_db)
):
    """WebSocket endpoint for real-time voice communication."""
    logger.info(f"🔌 WebSocket connection requested for session: {session_id}")

    try:
        await websocket.accept()
        logger.info(f"✅ WebSocket connection accepted for session: {session_id}")
    except Exception as e:
        logger.error(f"❌ Failed to accept WebSocket connection for {session_id}: {e}")
        return

    try:
        # Update router session status
        if session_id in active_sessions:
            active_sessions[session_id]["websocket_connected"] = True
            active_sessions[session_id]["status"] = "connected"

        # ✅ FIXED: Use the correct method signature - no model_name parameter
        logger.info(f"🎤 Creating voice session: {session_id}")
        success = await voice_agent.create_session(
            session_id, websocket
        )  # ✅ Correct call

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
                pass
            return

        logger.info(f"✅ Voice session created successfully: {session_id}")

        # Create database record for the session
        try:
            # Check if session already exists in DB (from start-session endpoint)
            existing_session = (
                db.query(DBVoiceSession)
                .filter(DBVoiceSession.session_id == session_id)
                .first()
            )

            if not existing_session:
                # Create new database session if it doesn't exist
                db_session = DBVoiceSession(
                    session_id=session_id,
                    user_id=None,  # We don't have user context in WebSocket
                    context="voice_chat",
                    status="connected",
                )
                db.add(db_session)
                db.commit()
                logger.info(f"✅ Database voice session created: {session_id}")
            else:
                # Update existing session status to connected
                existing_session.status = "connected"
                db.commit()
                logger.info(
                    f"✅ Database voice session updated to connected: {session_id}"
                )
        except Exception as e:
            logger.warning(
                f"Failed to create/update DB voice session {session_id}: {e}"
            )
            # Don't fail the WebSocket connection due to DB issues
            db.rollback()

        # The voice_agent.create_session() handles the WebSocket communication loop
        # No additional message handling needed here since it's handled in the service

    except WebSocketDisconnect:
        logger.info(f"🔌 WebSocket disconnected: {session_id}")
    except Exception as e:
        logger.error(f"❌ WebSocket endpoint error for {session_id}: {e}")
    finally:
        logger.info(f"🧹 Cleaning up session: {session_id}")

        # Update router session status
        if session_id in active_sessions:
            active_sessions[session_id]["websocket_connected"] = False
            active_sessions[session_id]["status"] = "disconnected"

        # Cleanup is handled by the voice_agent service
        try:
            await voice_agent.stop_session(session_id)
            logger.info(f"✅ Session cleanup completed: {session_id}")
        except Exception as e:
            logger.warning(f"Error during session cleanup for {session_id}: {e}")

        # Update database session status to "stopped"
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
                logger.info(
                    f"✅ Database voice session updated to stopped: {session_id}"
                )
            else:
                logger.warning(f"Database voice session not found: {session_id}")
        except Exception as e:
            logger.warning(f"Failed to update DB voice session {session_id}: {e}")
            # Rollback in case of error
            db.rollback()


# ✅ Updated health check
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

        # ✅ Updated audio system check
        health_status["checks"]["audio_system"] = "client-side WebSocket streaming"
        health_status["checks"]["pyaudio_required"] = False

        # Check active sessions
        router_sessions = len(active_sessions)
        websocket_sessions = len(voice_agent.active_sessions)
        health_status["checks"]["router_sessions"] = router_sessions
        health_status["checks"]["websocket_sessions"] = websocket_sessions

        # ✅ Check available models
        health_status["checks"]["available_models"] = [
            "gemini-2.0-flash-live-001",
            "gemini-live-2.5-flash-preview",
            "gemini-2.5-flash-preview-native-audio-dialog",
        ]

        # ✅ NEW: Persona configuration support
        health_status["checks"]["persona_support"] = True
        health_status["checks"]["available_configs"] = [
            "persona-audio",
            "audio-only-fallback",
            "text-only",
            "bare",
        ]

        # Count persona sessions
        persona_sessions = sum(
            1
            for session in active_sessions.values()
            if session.get("session_type") == "persona"
        )
        health_status["checks"]["persona_sessions"] = persona_sessions

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
