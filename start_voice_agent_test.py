"""
Quick start script for testing the voice agent
"""

import asyncio
import subprocess
import sys
import time
from loguru import logger


def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        import pyaudio
        import google.generativeai as genai

        logger.success("✅ All dependencies are installed")
        return True
    except ImportError as e:
        logger.error(f"❌ Missing dependency: {e}")
        logger.info(
            "Install missing dependencies with: pip install pyaudio google-generativeai"
        )
        return False


def check_environment():
    """Check if environment variables are set."""
    import os

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logger.error("❌ GEMINI_API_KEY not found in environment variables")
        logger.info("Please set your Gemini API key in the .env file")
        return False

    logger.success("✅ Environment variables are configured")
    return True


async def test_voice_service():
    """Test the voice agent service directly."""
    try:
        from services.voice_agent_service import voice_agent_service

        logger.info("🧪 Testing voice agent service...")

        # Test session start
        success = await voice_agent_service.start_session()
        if success:
            logger.success("✅ Voice agent session started")

            # Test text message
            await voice_agent_service.send_text_message(
                "Hello! Can you help me create an anime character?"
            )
            logger.success("✅ Text message sent")

            # Wait briefly
            await asyncio.sleep(2)

            # Stop session
            await voice_agent_service.stop_session()
            logger.success("✅ Voice agent session stopped")

            return True
        else:
            logger.error("❌ Failed to start voice agent session")
            return False

    except Exception as e:
        logger.error(f"❌ Voice service test failed: {e}")
        return False


def start_server():
    """Start the FastAPI server."""
    logger.info("🚀 Starting FastAPI server...")

    try:
        # Start server in background
        process = subprocess.Popen(
            [sys.executable, "main.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        # Wait a bit for server to start
        time.sleep(3)

        # Check if process is still running
        if process.poll() is None:
            logger.success("✅ Server started successfully")
            logger.info("🌐 Server running at: http://localhost:8000")
            logger.info("📚 API docs available at: http://localhost:8000/docs")
            logger.info(
                "🎤 Voice agent endpoints at: http://localhost:8000/api/v1/voice"
            )
            return process
        else:
            stdout, stderr = process.communicate()
            logger.error(f"❌ Server failed to start: {stderr.decode()}")
            return None

    except Exception as e:
        logger.error(f"❌ Failed to start server: {e}")
        return None


async def test_api_endpoints():
    """Test the voice agent API endpoints."""
    import aiohttp

    base_url = "http://localhost:8000/api/v1"

    try:
        async with aiohttp.ClientSession() as session:
            # Test health endpoint
            logger.info("🏥 Testing health endpoint...")
            async with session.get(f"{base_url}/voice/health") as response:
                if response.status == 200:
                    data = await response.json()
                    logger.success(f"✅ Health check passed: {data['status']}")
                else:
                    logger.error(f"❌ Health check failed: {response.status}")
                    return False

            # Test info endpoint
            logger.info("ℹ️ Testing info endpoint...")
            async with session.get(f"{base_url}/voice") as response:
                if response.status == 200:
                    data = await response.json()
                    logger.success(f"✅ Info endpoint works: {data['service']}")
                else:
                    logger.error(f"❌ Info endpoint failed: {response.status}")
                    return False

            return True

    except Exception as e:
        logger.error(f"❌ API endpoint test failed: {e}")
        return False


async def main():
    """Main test function."""
    logger.info("🎤 Voice Agent Test Suite")
    logger.info("=" * 50)

    # Check dependencies
    if not check_dependencies():
        return False

    # Check environment
    if not check_environment():
        return False

    # Test voice service directly
    logger.info("\n📋 Testing Voice Service...")
    service_test = await test_voice_service()

    if not service_test:
        logger.error("❌ Voice service test failed")
        return False

    # Start server
    logger.info("\n🚀 Starting Server...")
    server_process = start_server()

    if not server_process:
        return False

    try:
        # Test API endpoints
        logger.info("\n🌐 Testing API Endpoints...")
        api_test = await test_api_endpoints()

        if api_test:
            logger.success("\n🎉 All tests passed!")
            logger.info("\nYou can now:")
            logger.info("1. Visit http://localhost:8000/docs for API documentation")
            logger.info(
                "2. Run 'python voice_agent_client_example.py' to test the client"
            )
            logger.info("3. Use the voice agent endpoints in your application")
            logger.info("\nPress Ctrl+C to stop the server")

            # Keep server running
            try:
                server_process.wait()
            except KeyboardInterrupt:
                logger.info("\n🛑 Stopping server...")
                server_process.terminate()
                server_process.wait()
                logger.success("✅ Server stopped")
        else:
            logger.error("❌ API endpoint tests failed")
            server_process.terminate()
            return False

    except Exception as e:
        logger.error(f"❌ Test suite failed: {e}")
        if server_process:
            server_process.terminate()
        return False

    return True


if __name__ == "__main__":
    # Load environment variables
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        logger.warning(
            "⚠️ python-dotenv not installed, make sure environment variables are set"
        )

    # Run tests
    success = asyncio.run(main())

    if success:
        logger.success("🎉 Voice Agent is ready to use!")
    else:
        logger.error("❌ Voice Agent setup failed")
        sys.exit(1)
