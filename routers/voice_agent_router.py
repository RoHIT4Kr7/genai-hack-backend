"""
Voice Agent Router for Anime Generation
Provides REST endpoints for voice interaction and transcription
"""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from typing import Dict, Any, List, Optional
from loguru import logger
from datetime import datetime
import asyncio
import json

from models.schemas import BaseModel
from services.voice_agent_service import voice_agent_service
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
async def start_voice_session(request: VoiceSessionRequest) -> VoiceSessionResponse:
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

        async def response_callback(text: str):
            """Handle AI responses."""
            logger.info(f"🤖 AI Response [{session_id}]: {text}")
            # Store response in session data
            if session_id in active_sessions:
                active_sessions[session_id]["last_response"] = {
                    "text": text,
                    "timestamp": create_timestamp(),
                }

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
            "user_id": request.user_id,
            "context": request.context,
            "started_at": create_timestamp(),
            "status": "active",
            "last_transcription": None,
            "last_response": None,
        }

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
async def stop_voice_session(session_id: str) -> VoiceSessionResponse:
    """
    Stop an active voice agent session.

    Args:
        session_id: The ID of the session to stop
    """
    try:
        logger.info(f"🛑 Stopping voice session: {session_id}")

        if session_id not in active_sessions:
            raise HTTPException(
                status_code=404, detail=f"Voice session {session_id} not found"
            )

        # Stop the voice agent service
        await voice_agent_service.stop_session(session_id)

        # Update session status
        active_sessions[session_id]["status"] = "stopped"
        active_sessions[session_id]["stopped_at"] = create_timestamp()

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
async def send_text_message(request: TextMessageRequest) -> Dict[str, Any]:
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
        success = await voice_agent_service.send_text_message(request.session_id, request.message)

        if not success:
            raise HTTPException(
                status_code=500, detail="Failed to send message to voice agent"
            )

        # Update session with sent message
        active_sessions[request.session_id]["last_sent_message"] = {
            "text": request.message,
            "timestamp": create_timestamp(),
        }

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


@router.websocket("/voice/ws/{session_id}")
async def voice_websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time voice agent communication.

    Provides real-time updates for:
    - Transcription results
    - AI responses
    - Session status changes
    - Error notifications
    """
    await websocket.accept()
    logger.info(f"🔌 WebSocket connected for voice session: {session_id}")

    try:
        # Check if session exists
        if session_id not in active_sessions:
            await websocket.send_json(
                {
                    "type": "error",
                    "message": f"Voice session {session_id} not found",
                    "timestamp": create_timestamp(),
                }
            )
            await websocket.close()
            return

        # Send initial status
        await websocket.send_json(
            {
                "type": "session_status",
                "session_id": session_id,
                "status": active_sessions[session_id]["status"],
                "message": "WebSocket connected to voice session",
                "timestamp": create_timestamp(),
            }
        )

        # Keep connection alive and send updates
        last_transcription = None
        last_response = None

        while True:
            try:
                # Check for new transcriptions
                current_transcription = active_sessions[session_id].get(
                    "last_transcription"
                )
                if (
                    current_transcription
                    and current_transcription != last_transcription
                ):
                    await websocket.send_json(
                        {
                            "type": "transcription",
                            "session_id": session_id,
                            "text": current_transcription["text"],
                            "timestamp": current_transcription["timestamp"],
                        }
                    )
                    last_transcription = current_transcription

                # Check for new responses
                current_response = active_sessions[session_id].get("last_response")
                if current_response and current_response != last_response:
                    await websocket.send_json(
                        {
                            "type": "ai_response",
                            "session_id": session_id,
                            "text": current_response["text"],
                            "timestamp": current_response["timestamp"],
                        }
                    )
                    last_response = current_response

                # Check if session is still active
                if active_sessions[session_id]["status"] != "active":
                    await websocket.send_json(
                        {
                            "type": "session_ended",
                            "session_id": session_id,
                            "message": "Voice session has ended",
                            "timestamp": create_timestamp(),
                        }
                    )
                    break

                await asyncio.sleep(0.5)  # Check for updates every 500ms

            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket error for session {session_id}: {e}")
                await websocket.send_json(
                    {
                        "type": "error",
                        "message": f"WebSocket error: {str(e)}",
                        "timestamp": create_timestamp(),
                    }
                )
                break

    except WebSocketDisconnect:
        logger.info(f"🔌 WebSocket disconnected for voice session: {session_id}")
    except Exception as e:
        logger.error(f"❌ WebSocket error for session {session_id}: {e}")
    finally:
        logger.info(f"🔌 WebSocket connection closed for voice session: {session_id}")
        
        # CRITICAL: Stop the voice agent session when WebSocket disconnects
        try:
            if session_id in active_sessions:
                logger.info(f"🛑 Auto-stopping voice session due to WebSocket disconnect: {session_id}")
                await voice_agent_service.stop_session(session_id)
                
                # Update session status
                if session_id in active_sessions:
                    active_sessions[session_id]["status"] = "stopped"
                    active_sessions[session_id]["stopped_at"] = create_timestamp()
                    
                logger.success(f"✅ Voice session {session_id} stopped due to WebSocket disconnect")
        except Exception as cleanup_error:
            logger.error(f"❌ Error during WebSocket disconnect cleanup: {cleanup_error}")


@router.get("/voice/health")
async def voice_agent_health() -> Dict[str, Any]:
    """
    Health check endpoint for voice agent service.

    Checks:
    - Google Gemini API connectivity
    - Audio system availability
    - Active sessions status
    """
    try:
        health_status = {
            "service": "voice_agent",
            "status": "healthy",
            "timestamp": create_timestamp(),
            "checks": {},
        }

        # Check Gemini API key
        import os

        gemini_key = os.environ.get("GEMINI_API_KEY")
        health_status["checks"]["gemini_api_key"] = (
            "configured" if gemini_key else "missing"
        )

        # Check PyAudio availability
        try:
            import pyaudio

            pya = pyaudio.PyAudio()
            device_count = pya.get_device_count()
            pya.terminate()
            health_status["checks"][
                "audio_system"
            ] = f"available ({device_count} devices)"
        except Exception as e:
            health_status["checks"]["audio_system"] = f"error: {str(e)}"
            health_status["status"] = "degraded"

        # Check active sessions
        active_count = len(
            [s for s in active_sessions.values() if s["status"] == "active"]
        )
        health_status["checks"]["active_sessions"] = active_count

        # Overall health determination
        if health_status["checks"]["gemini_api_key"] == "missing":
            health_status["status"] = "unhealthy"

        return health_status

    except Exception as e:
        logger.error(f"❌ Voice agent health check failed: {e}")
        return {
            "service": "voice_agent",
            "status": "unhealthy",
            "error": str(e),
            "timestamp": create_timestamp(),
        }


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
