"""
Dhyaan (Meditation) Router for personalized meditation generation.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from loguru import logger

from models.schemas import MeditationRequest, MeditationResponse
from utils.auth import get_current_user
from models.user import User
from sqlalchemy.orm import Session
from models.db import get_db
from models.dhyaan import MeditationSession as DBMeditationSession
from models.dhyaan import DhyaanCheckin as DBDhyaanCheckin
from datetime import datetime, timedelta
from pydantic import BaseModel, Field

# Import dhyaan service with error handling
try:
    from services.dhyaan_service import dhyaan_service

    logger.info("✅ DhyaanService imported successfully in router")
except Exception as e:
    logger.error(f"❌ Failed to import DhyaanService in router: {e}")
    dhyaan_service = None

router = APIRouter(tags=["Dhyaan/Meditation"])
logger.info("🧘 Dhyaan router initialized")


@router.post("/generate-meditation", response_model=MeditationResponse)
async def generate_meditation(
    request: MeditationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generate a personalized guided meditation based on user's current and desired feelings.

    This endpoint:
    1. Accepts user's current feeling, desired feeling, and experience level
    2. Generates a personalized meditation script using Gemini AI
    3. Creates meditation audio using Gemini 2.5 Flash TTS
    4. Downloads appropriate background music from GCS
    5. Returns URLs for both meditation audio and background music

    Args:
        request: MeditationRequest containing user inputs

    Returns:
        MeditationResponse with meditation details and audio URLs
    """
    try:
        # Check if dhyaan service is available
        if dhyaan_service is None:
            logger.error("DhyaanService is not initialized")
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "Meditation service is not available",
                    "message": "The meditation service failed to initialize. Please check server logs.",
                    "type": "service_unavailable",
                },
            )

        logger.info(
            f"🧘 Meditation generation requested: {request.inputs.currentFeeling} → "
            f"{request.inputs.desiredFeeling} ({request.inputs.experience})"
        )

        # Generate personalized meditation
        meditation_data = await dhyaan_service.generate_meditation(
            current_feeling=request.inputs.currentFeeling,
            desired_feeling=request.inputs.desiredFeeling,
            experience=request.inputs.experience,
        )

        # Create response
        response = MeditationResponse(**meditation_data)

        logger.info(f"✅ Meditation generated successfully: {response.meditation_id}")

        # Persist meditation session
        try:
            db_item = DBMeditationSession(
                meditation_id=response.meditation_id,
                user_id=current_user.id,
                current_feeling=request.inputs.currentFeeling,
                desired_feeling=request.inputs.desiredFeeling,
                experience=request.inputs.experience,
                title=response.title,
                duration=response.duration,
                audio_url=response.audio_url,
                background_music_url=response.background_music_url,
                script=response.script,
                guidance_type=response.guidance_type,
            )
            db.add(db_item)
            db.commit()
        except Exception as e:
            logger.warning(
                f"Failed to persist meditation session {response.meditation_id}: {e}"
            )
        return response

    except ValueError as e:
        logger.error(f"Validation error in meditation generation: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"Failed to generate meditation: {e}")
        # Ensure we return a proper JSON error response
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error during meditation generation",
                "message": "Please try again. If the problem persists, contact support.",
                "type": "meditation_generation_error",
            },
        )


class DhyaanCheckinRequest(BaseModel):
    mood_score: int = Field(..., ge=1, le=5)
    journal_entry: str | None = None


@router.post("/dhyaan/checkin")
async def create_checkin(
    payload: DhyaanCheckinRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        item = DBDhyaanCheckin(
            user_id=current_user.id,
            mood_score=payload.mood_score,
            journal_entry=payload.journal_entry,
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return {
            "id": item.id,
            "mood_score": item.mood_score,
            "journal_entry": item.journal_entry,
            "created_at": item.created_at.isoformat() if item.created_at else None,
        }
    except Exception as e:
        logger.error(f"Failed to create dhyaan checkin: {e}")
        raise HTTPException(status_code=500, detail="Failed to create checkin")


@router.get("/dhyaan/checkins")
async def list_checkins(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        cutoff = datetime.utcnow() - timedelta(days=max(1, min(days, 90)))
        rows = (
            db.query(DBDhyaanCheckin)
            .filter(DBDhyaanCheckin.user_id == current_user.id)
            .filter(DBDhyaanCheckin.created_at >= cutoff)
            .order_by(DBDhyaanCheckin.created_at.desc())
            .all()
        )
        return [
            {
                "id": r.id,
                "mood_score": r.mood_score,
                "journal_entry": r.journal_entry,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ]
    except Exception as e:
        logger.error(f"Failed to list dhyaan checkins: {e}")
        raise HTTPException(status_code=500, detail="Failed to list checkins")


@router.get("/meditation-options")
async def get_meditation_options():
    """
    Get available options for meditation generation.

    Returns:
        Available current feelings, desired feelings, and experience levels
    """
    return JSONResponse(
        content={
            "currentFeelings": [
                "sad",
                "upset",
                "anxious",
                "fearful",
                "lonely",
                "guilty",
                "depressed",
            ],
            "desiredFeelings": ["joy", "love", "peaceful", "gratitude", "acceptance"],
            "experienceLevels": ["beginner", "intermediate", "advanced"],
            "guidanceTypes": [
                "breathing",
                "body_scan",
                "visualization",
                "affirmation",
                "loving_kindness",
            ],
        }
    )


@router.get("/dhyaan-test")
async def dhyaan_test():
    """Simple test endpoint to verify the dhyaan router is working."""
    return JSONResponse(
        content={
            "message": "Dhyaan router is working!",
            "service": "dhyaan",
            "status": "router_active",
            "dhyaan_service_available": dhyaan_service is not None,
        }
    )


@router.get("/health")
async def dhyaan_health_check():
    """Health check endpoint for the meditation service."""
    try:
        # Basic service health check
        health_status = {
            "service": "dhyaan",
            "status": (
                "healthy" if dhyaan_service is not None else "service_unavailable"
            ),
            "timestamp": "2025-01-17T10:30:00Z",
            "components": {
                "gemini_llm": (
                    "available" if dhyaan_service is not None else "unavailable"
                ),
                "gemini_tts": (
                    "available" if dhyaan_service is not None else "unavailable"
                ),
                "gcs_storage": (
                    "available" if dhyaan_service is not None else "unavailable"
                ),
                "music_metadata": (
                    "loaded" if dhyaan_service is not None else "not_loaded"
                ),
            },
        }

        return JSONResponse(content=health_status)

    except Exception as e:
        logger.error(f"Dhyaan health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"service": "dhyaan", "status": "unhealthy", "error": str(e)},
        )
