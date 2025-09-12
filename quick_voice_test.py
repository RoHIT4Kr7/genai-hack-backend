"""
Quick test of voice agent endpoints
"""

import asyncio
import aiohttp
from loguru import logger


async def test_voice_endpoints():
    """Quick test of voice agent endpoints."""

    base_url = "http://localhost:8000/api/v1"

    try:
        async with aiohttp.ClientSession() as session:
            # Test health endpoint
            logger.info("🏥 Testing voice agent health...")
            async with session.get(f"{base_url}/voice/health") as response:
                if response.status == 200:
                    data = await response.json()
                    logger.success(f"✅ Health check: {data['status']}")
                    print(f"Health Status: {data['status']}")
                    print(f"Checks: {data['checks']}")
                else:
                    logger.error(f"❌ Health check failed: {response.status}")
                    return False

            # Test info endpoint
            logger.info("ℹ️ Testing voice agent info...")
            async with session.get(f"{base_url}/voice") as response:
                if response.status == 200:
                    data = await response.json()
                    logger.success(f"✅ Service: {data['service']}")
                    print(f"\nService: {data['service']}")
                    print(f"Features: {len(data['features'])} available")
                    print(f"Endpoints: {len(data['endpoints'])} available")
                else:
                    logger.error(f"❌ Info endpoint failed: {response.status}")
                    return False

            # Test start session
            logger.info("🎤 Testing session start...")
            session_data = {"user_id": "test_user", "context": "anime_generation"}

            async with session.post(
                f"{base_url}/voice/start-session", json=session_data
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    session_id = data["session_id"]
                    logger.success(f"✅ Session started: {session_id}")
                    print(f"\nSession ID: {session_id}")

                    # Test send message
                    logger.info("📝 Testing send message...")
                    message_data = {
                        "session_id": session_id,
                        "message": "Help me create a magical girl anime character!",
                    }

                    async with session.post(
                        f"{base_url}/voice/send-message", json=message_data
                    ) as msg_response:
                        if msg_response.status == 200:
                            msg_data = await msg_response.json()
                            logger.success("✅ Message sent successfully")
                            print(f"Message Status: {msg_data['status']}")
                        else:
                            logger.error(
                                f"❌ Send message failed: {msg_response.status}"
                            )

                    # Wait a bit
                    await asyncio.sleep(2)

                    # Test session status
                    logger.info("📊 Testing session status...")
                    async with session.get(
                        f"{base_url}/voice/session/{session_id}/status"
                    ) as status_response:
                        if status_response.status == 200:
                            status_data = await status_response.json()
                            logger.success("✅ Session status retrieved")
                            print(f"Session Status: {status_data['status']}")
                            if status_data.get("last_response"):
                                print(
                                    f"AI Response: {status_data['last_response']['text'][:100]}..."
                                )
                        else:
                            logger.error(
                                f"❌ Session status failed: {status_response.status}"
                            )

                    # Test stop session
                    logger.info("🛑 Testing session stop...")
                    async with session.post(
                        f"{base_url}/voice/stop-session?session_id={session_id}"
                    ) as stop_response:
                        if stop_response.status == 200:
                            stop_data = await stop_response.json()
                            logger.success("✅ Session stopped successfully")
                            print(f"Stop Status: {stop_data['status']}")
                        else:
                            logger.error(
                                f"❌ Stop session failed: {stop_response.status}"
                            )

                else:
                    logger.error(f"❌ Start session failed: {response.status}")
                    return False

            return True

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False


if __name__ == "__main__":
    print("🎤 Voice Agent Quick Test")
    print("=" * 40)
    print("Make sure the server is running on http://localhost:8000")
    print("=" * 40)

    result = asyncio.run(test_voice_endpoints())

    if result:
        print("\n🎉 All voice agent endpoints are working!")
    else:
        print("\n❌ Some tests failed. Check the server logs.")
