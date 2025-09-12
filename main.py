import asyncio
import base64
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from loguru import logger
import sys
import socketio

from config.settings import settings
from routers.manga_router import router as manga_router
from routers.voice_agent_router import router as voice_agent_router


# Create Socket.IO server
sio = socketio.AsyncServer(
    async_mode="asgi",
    # Avoid duplicate CORS headers with FastAPI CORSMiddleware; let FastAPI handle CORS
    cors_allowed_origins=[],
    logger=True,
    engineio_logger=True,
)

# Create ASGI app that combines FastAPI and Socket.IO
socket_app = socketio.ASGIApp(sio, socketio_path="socket.io")

# Import socket utilities
from utils.socket_utils import (
    emit_generation_progress,
    add_active_generation,
    get_active_generation,
    remove_active_generation,
    get_all_active_generations,
    active_generations,
)


# Use the emit_generation_progress function from socket_utils


# Socket.IO event handlers
@sio.event
async def connect(sid, environ):
    logger.info(f"Client connected: {sid}")
    # Auto-join a global progress room so clients can receive progress updates even
    # before they know the concrete story_id (e.g., before HTTP response returns)
    try:
        await sio.enter_room(sid, "progress_updates")
        logger.info(f"✅ Client {sid} entered progress_updates room on connect")
    except Exception as e:
        logger.warning(f"Failed to join progress_updates on connect for {sid}: {e}")

    await sio.emit("connected", {"data": "Connected successfully"}, room=sid)


@sio.event
async def disconnect(sid):
    logger.info(f"Client disconnected: {sid}")
    # Note: active_generations cleanup is handled by socket_utils


@sio.event
async def join_story_generation(sid, data):
    """Join a story generation session."""
    logger.info(f"🔗 join_story_generation called by {sid} with data: {data}")
    story_id = data.get("story_id")
    if story_id:
        # Join the client to the story-specific room
        await sio.enter_room(sid, story_id)
        logger.info(f"✅ Client {sid} entered room: {story_id}")

        # Also join the general progress room
        await sio.enter_room(sid, "progress_updates")
        logger.info(f"✅ Client {sid} entered progress_updates room")

        add_active_generation(
            story_id, {"sid": sid, "joined_at": asyncio.get_event_loop().time()}
        )
        logger.info(f"✅ Client {sid} joined story generation room: {story_id}")
        await sio.emit("joined_generation", {"story_id": story_id}, room=sid)
    else:
        logger.warning(f"❌ No story_id provided in join_story_generation by {sid}")


@sio.event
async def start_audio_stream(sid, data):
    """Start streaming audio chunks to a client."""
    story_id = data.get("story_id")
    if story_id:
        logger.info(f"Client {sid} requested audio stream for story {story_id}")

        # Audio streaming is not available (removed streaming music service)
        await sio.emit(
            "audio_stream_error",
            {
                "story_id": story_id,
                "error": "Audio streaming not available - using static background music",
            },
            room=sid,
        )
    else:
        await sio.emit(
            "audio_stream_error",
            {"error": "Invalid request or not joined to story generation"},
            room=sid,
        )


@sio.event
async def stop_audio_stream(sid, data):
    """Stop streaming audio to a client."""
    story_id = data.get("story_id")
    if story_id:
        logger.info(f"Client {sid} stopped audio stream for story {story_id}")
        await sio.emit("audio_stream_stopped", {"story_id": story_id}, room=sid)


# Configure logging
def setup_logging():
    """Configure loguru logging."""
    logger.remove()  # Remove default handler

    # Add console handler with custom format
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO" if not settings.debug else "DEBUG",
        colorize=True,
    )

    # Add file handler for production
    logger.add(
        "logs/manga_wellness.log",
        rotation="10 MB",
        retention="7 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="INFO",
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Manga Wellness Backend...")
    setup_logging()

    # Initialize services
    try:
        from services.nano_banana_service import nano_banana_service
        from services.story_service import story_service
        from services.chirp3hd_tts_service import (
            chirp3hd_tts_service as audio_service,
        )

        logger.info("Nano-banana service with GCS and Chirp 3 HD initialized")

        logger.info("All services initialized successfully")

    except Exception as e:
        logger.error(f"Service initialization failed: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down Manga Wellness Backend...")


# Create FastAPI app
app = FastAPI(
    title="Manga Mental Wellness Backend",
    description="A mental wellness platform that generates personalized 6-panel manga stories for youth",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Mount Socket.IO app
app.mount("/socket.io", socket_app)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(manga_router, prefix="/api/v1")
app.include_router(voice_agent_router, prefix="/api/v1")


# Validation exception handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with detailed logging."""
    logger.error(f"🚨 Validation error on {request.method} {request.url}")

    # Try to get request body for debugging
    try:
        body = await request.body()
        if body:
            import json

            try:
                body_json = json.loads(body)
                logger.error(f"Request body: {json.dumps(body_json, indent=2)}")
            except:
                logger.error(f"Request body (raw): {body}")
    except Exception as e:
        logger.error(f"Could not read request body: {e}")

    logger.error(f"Validation exception details: {exc}")

    # Return the original validation error
    return JSONResponse(
        status_code=422,
        content=(
            exc.detail if hasattr(exc, "detail") else {"error": "Validation failed"}
        ),
    )


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "details": "An unexpected error occurred",
            "timestamp": asyncio.get_event_loop().time(),
        },
    )


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Manga Mental Wellness Backend",
        "version": "1.0.0",
        "description": "Generate personalized manga stories for mental wellness",
        "endpoints": {
            "docs": "/docs",
            "health": "/api/v1/health",
            "generate_manga": "/api/v1/generate-manga",
            "generate_manga_streaming": "/api/v1/generate-manga-streaming",
            "voice_agent": "/api/v1/voice",
            "voice_start_session": "/api/v1/voice/start-session",
            "voice_websocket": "/api/v1/voice/ws/{session_id}",
            "socket_io": "/socket.io/",
        },
    }


# Health check endpoint (simple)
@app.get("/health")
async def simple_health():
    """Simple health check endpoint."""
    return {"status": "healthy", "service": "manga-wellness-backend"}


if __name__ == "__main__":
    import uvicorn

    logger.info(f"Starting server on {settings.api_host}:{settings.api_port}")
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level="info",
    )
