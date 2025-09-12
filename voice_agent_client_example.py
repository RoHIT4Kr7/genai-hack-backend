"""
Voice Agent Client Example
Demonstrates how to interact with the voice agent endpoints
"""

import asyncio
import aiohttp
import json
from loguru import logger

# API base URL (adjust as needed)
BASE_URL = "http://localhost:8000/api/v1"


async def test_voice_agent_endpoints():
    """Test all voice agent endpoints."""

    async with aiohttp.ClientSession() as session:

        # 1. Check voice agent health
        logger.info("🏥 Checking voice agent health...")
        async with session.get(f"{BASE_URL}/voice/health") as response:
            health_data = await response.json()
            logger.info(f"Health status: {health_data}")

        # 2. Get voice agent info
        logger.info("ℹ️ Getting voice agent info...")
        async with session.get(f"{BASE_URL}/voice") as response:
            info_data = await response.json()
            logger.info(f"Service info: {info_data['service']}")

        # 3. Start a voice session
        logger.info("🎤 Starting voice session...")
        session_request = {
            "session_id": "test_session_001",
            "user_id": "test_user",
            "context": "anime_generation",
        }

        async with session.post(
            f"{BASE_URL}/voice/start-session", json=session_request
        ) as response:
            if response.status == 200:
                session_data = await response.json()
                session_id = session_data["session_id"]
                logger.success(f"✅ Voice session started: {session_id}")
            else:
                error_data = await response.json()
                logger.error(f"❌ Failed to start session: {error_data}")
                return

        # 4. Send a text message
        logger.info("📝 Sending text message...")
        message_request = {
            "session_id": session_id,
            "message": "Hi! I want to create an anime story about a magical school. Can you help me develop the main character?",
        }

        async with session.post(
            f"{BASE_URL}/voice/send-message", json=message_request
        ) as response:
            if response.status == 200:
                message_data = await response.json()
                logger.success("✅ Text message sent successfully")
            else:
                error_data = await response.json()
                logger.error(f"❌ Failed to send message: {error_data}")

        # 5. Wait a bit for processing
        await asyncio.sleep(2)

        # 6. Check session status
        logger.info("📊 Checking session status...")
        async with session.get(
            f"{BASE_URL}/voice/session/{session_id}/status"
        ) as response:
            if response.status == 200:
                status_data = await response.json()
                logger.info(f"Session status: {status_data['status']}")
                if status_data.get("last_transcription"):
                    logger.info(
                        f"Last transcription: {status_data['last_transcription']['text']}"
                    )
                if status_data.get("last_response"):
                    logger.info(
                        f"Last AI response: {status_data['last_response']['text']}"
                    )
            else:
                error_data = await response.json()
                logger.error(f"❌ Failed to get status: {error_data}")

        # 7. List all sessions
        logger.info("📋 Listing all sessions...")
        async with session.get(f"{BASE_URL}/voice/sessions") as response:
            sessions_data = await response.json()
            logger.info(f"Total sessions: {sessions_data['total_sessions']}")
            logger.info(f"Active sessions: {sessions_data['active_sessions']}")

        # 8. Stop the session
        logger.info("🛑 Stopping voice session...")
        async with session.post(
            f"{BASE_URL}/voice/stop-session?session_id={session_id}"
        ) as response:
            if response.status == 200:
                stop_data = await response.json()
                logger.success(f"✅ Voice session stopped: {stop_data['message']}")
            else:
                error_data = await response.json()
                logger.error(f"❌ Failed to stop session: {error_data}")


async def test_websocket_connection():
    """Test WebSocket connection for real-time updates."""
    import websockets

    session_id = "test_websocket_session"
    ws_url = f"ws://localhost:8000/api/v1/voice/ws/{session_id}"

    try:
        logger.info(f"🔌 Connecting to WebSocket: {ws_url}")

        async with websockets.connect(ws_url) as websocket:
            logger.success("✅ WebSocket connected")

            # Listen for messages for a few seconds
            try:
                while True:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(message)
                    logger.info(f"📨 WebSocket message: {data}")

                    if data.get("type") == "error":
                        logger.warning(f"WebSocket error: {data['message']}")
                        break

            except asyncio.TimeoutError:
                logger.info("⏰ WebSocket timeout - no more messages")

    except Exception as e:
        logger.error(f"❌ WebSocket connection failed: {e}")


if __name__ == "__main__":
    logger.info("🚀 Starting Voice Agent Client Example...")

    # Test REST endpoints
    asyncio.run(test_voice_agent_endpoints())

    print("\n" + "=" * 50)
    print("Voice Agent Client Example completed!")
    print("=" * 50)

    # Uncomment to test WebSocket (requires active session)
    # print("\nTesting WebSocket connection...")
    # asyncio.run(test_websocket_connection())
