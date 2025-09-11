from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Dict, Any
from loguru import logger
from datetime import datetime

from models.schemas import (
    StoryInputs,
    GeneratedStory,
    StoryGenerationRequest,
    StoryGenerationResponse,
    HealthResponse,
)
from services.story_service import story_service
from services.sequential_story_service import sequential_story_service
from services.image_service import image_service
from services.audio_service import audio_service
from services.storage_service import storage_service
from utils.helpers import create_timestamp, log_api_call
from utils.socket_utils import emit_generation_progress

# Create router instance
router = APIRouter()


@router.post("/generate-manga", response_model=StoryGenerationResponse)
async def generate_manga_story(
    request: StoryGenerationRequest,
) -> StoryGenerationResponse:
    """
    Generate a complete 6-panel manga story for mental wellness.

    This endpoint orchestrates the complete pipeline:
    1. Story planning with Mangaka-Sensei
    2. Image generation with Imagen 4.0
    3. Audio generation with personalized voices (background music and TTS)
    4. Final delivery with separate audio files
    """
    try:
        logger.info(
            f"🎬 Manga generation request received for: {request.inputs.nickname}"
        )
        log_api_call("/generate-manga", request.dict())

        # Validate inputs
        if not request.inputs.nickname:
            raise HTTPException(status_code=400, detail="Nickname is required")

        # Generate the complete story using the orchestrated workflow
        story = await story_service.generate_complete_story(request.inputs)

        if not story or story.status != "completed":
            raise HTTPException(
                status_code=500, detail="Story generation failed or incomplete"
            )

        # Create success response
        manga_title = (
            getattr(request.inputs, "mangaTitle", None)
            or f"{request.inputs.nickname}'s Journey"
        )
        response = StoryGenerationResponse(
            story_id=story.story_id,
            status="completed",
            message=f"Manga story '{manga_title}' generated successfully!",
            story=story,
        )

        logger.success(f"✅ Manga story generated: {story.story_id}")
        log_api_call("/generate-manga", request.dict(), response.dict())

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Manga generation failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Story generation failed: {str(e)}"
        )


@router.post("/test-minimal", response_model=StoryGenerationResponse)
async def test_minimal_generation(
    request: StoryGenerationRequest,
) -> StoryGenerationResponse:
    """Minimal test endpoint to isolate hanging issues."""
    try:
        logger.info(f"🧪 Minimal test for: {request.inputs.nickname}")

        # Just return a simple response without any processing
        response = StoryGenerationResponse(
            story_id="test_123",
            status="completed",
            message="Minimal test successful!",
            story=None,
        )

        logger.info("✅ Minimal test completed")
        return response

    except Exception as e:
        logger.error(f"❌ Minimal test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-manga-streaming", response_model=StoryGenerationResponse)
async def generate_manga_story_streaming(
    request: StoryGenerationRequest,
) -> StoryGenerationResponse:
    """
    Generate a 6-panel manga story using parallel panel processing.

    This endpoint generates all 6 panels simultaneously and starts the slideshow
    only when ALL assets (images, audio, music) are ready, providing real-time
    progress updates via Socket.IO.

    The frontend should:
    1. Connect to Socket.IO endpoint
    2. Call this endpoint to start generation
    3. Listen for real-time progress events
    4. Wait for 'slideshow_start' event with all_panels_ready: True

    Args:
        request: Story generation request with user inputs

    Returns:
        Story generation response (panels will be delivered via Socket.IO)
    """
    try:
        logger.info(
            f"🎬 Streaming manga generation request received for: {request.inputs.nickname}"
        )
        log_api_call("/generate-manga-streaming", request.dict())

        # Validate inputs
        if not request.inputs.nickname:
            raise HTTPException(status_code=400, detail="Nickname is required")

        # Create progress emitter function that captures the request context
        async def emit_progress(event_type: str, data: dict):
            story_id = data.get("story_id", "")
            return await emit_generation_progress(story_id, event_type, data)

        # Generate the complete story using sequential workflow for better reliability
        story_data = await sequential_story_service.generate_sequential_story(
            inputs=request.inputs,
            emit_progress=emit_progress,
            user_age=request.inputs.age,
            user_gender=request.inputs.gender,
        )

        if not story_data or story_data.status != "completed":
            raise HTTPException(
                status_code=500,
                detail="Sequential story generation failed or incomplete",
            )

        # Create success response
        manga_title = (
            getattr(request.inputs, "mangaTitle", None)
            or f"{request.inputs.nickname}'s Journey"
        )
        response = StoryGenerationResponse(
            story_id=story_data.story_id,
            status="completed",
            message=f"Manga story '{manga_title}' generated successfully with sequential processing!",
            story=story_data.story,  # Include the story data
        )

        logger.success(f"✅ Sequential manga story generated: {story_data.story_id}")
        log_api_call("/generate-manga-streaming", request.dict(), response.dict())

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Sequential manga generation failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Sequential story generation failed: {str(e)}"
        )


@router.get("/story/{story_id}/status")
async def get_story_status(story_id: str) -> Dict[str, Any]:
    """Get the status of a story generation."""
    try:
        status = await story_service.get_story_status(story_id)
        return status

    except Exception as e:
        logger.error(f"Failed to get story status: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get story status: {str(e)}"
        )


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint to verify all services are operational.

    Checks:
    - ChatVertexAI (Story generation)
    - Imagen 4.0 (Image generation)
    - Google Cloud TTS (Voice generation)
    - Lyria-002 (Music generation)
    - Google Cloud Storage (Asset storage)
    """
    try:
        services_status = {}

        # Check Story service (ChatVertexAI)
        try:
            if story_service.llm is not None:
                services_status["story_service"] = "healthy"
            else:
                services_status["story_service"] = "unhealthy - LLM not initialized"
        except Exception as e:
            services_status["story_service"] = f"error - {str(e)}"

        # Check Image service (Imagen)
        try:
            if image_service.model is not None:
                services_status["image_service"] = "healthy"
            else:
                services_status["image_service"] = "unhealthy - Imagen not initialized"
        except Exception as e:
            services_status["image_service"] = f"error - {str(e)}"

        # Check Audio service (TTS only, Lyria removed)
        try:
            if audio_service.tts_client is not None:
                services_status["audio_service"] = "healthy"
            else:
                services_status["audio_service"] = (
                    "unhealthy - TTS client not initialized"
                )
        except Exception as e:
            services_status["audio_service"] = f"error - {str(e)}"

        # Check Storage service (GCS)
        try:
            if storage_service.client is not None:
                services_status["storage_service"] = "healthy"
            else:
                services_status["storage_service"] = "unhealthy - GCS not initialized"
        except Exception as e:
            services_status["storage_service"] = f"error - {str(e)}"

        # Determine overall health
        all_healthy = all("healthy" in status for status in services_status.values())
        overall_status = "healthy" if all_healthy else "degraded"

        response = HealthResponse(
            status=overall_status,
            timestamp=create_timestamp(),
            services=services_status,
        )

        logger.info(f"Health check completed: {overall_status}")
        return response

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@router.get("/test-simple")
async def test_simple():
    """Ultra simple test endpoint."""
    logger.info("🧪 Simple GET test")
    return {"status": "ok", "message": "Simple test works"}


@router.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Manga Mental Wellness Backend API",
        "version": "1.0.0",
        "description": "Generate personalized 6-panel manga stories for youth mental wellness",
        "endpoints": {
            "generate_manga": "/generate-manga",
            "generate_manga_streaming": "/generate-manga-streaming",
            "health": "/health",
            "story_status": "/story/{story_id}/status",
        },
        "features": [
            "Mangaka-Sensei AI storytelling",
            "Imagen 4.0 image generation",
            "Personalized voice selection (age/gender)",
            "Lyria-002 background music",
            "Separate background music and TTS audio files",
            "Streaming panel-by-panel generation",
            "Real-time progress updates via Socket.IO",
            "Immediate asset generation per panel",
        ],
    }
