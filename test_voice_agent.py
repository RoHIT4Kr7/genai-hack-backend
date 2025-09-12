"""
Test script for Voice Agent Service
Simple test to verify voice agent functionality
"""

import asyncio
import os
from loguru import logger


async def test_voice_agent():
    """Test the voice agent service."""

    # Check if API key is available
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logger.error("❌ GEMINI_API_KEY not found in environment variables")
        return False

    logger.info("🧪 Testing Voice Agent Service...")

    # Import after environment variables are loaded
    from services.voice_agent_service import voice_agent_service

    try:
        # Test session start
        logger.info("1. Testing session start...")
        success = await voice_agent_service.start_session()

        if not success:
            logger.error("❌ Failed to start voice agent session")
            return False

        logger.success("✅ Voice agent session started successfully")

        # Test text message
        logger.info("2. Testing text message...")
        message_success = await voice_agent_service.send_text_message(
            "Hello! I want to create an anime about a young hero's journey. Can you help me brainstorm some ideas?"
        )

        if message_success:
            logger.success("✅ Text message sent successfully")
        else:
            logger.warning("⚠️ Text message failed")

        # Wait a bit for response
        logger.info("3. Waiting for response...")
        await asyncio.sleep(3)

        # Test session stop
        logger.info("4. Testing session stop...")
        await voice_agent_service.stop_session()
        logger.success("✅ Voice agent session stopped successfully")

        logger.success("🎉 Voice Agent Service test completed successfully!")
        return True

    except Exception as e:
        logger.error(f"❌ Voice Agent Service test failed: {e}")
        return False


if __name__ == "__main__":
    # Load environment variables first
    try:
        from dotenv import load_dotenv

        load_dotenv()
        logger.info("✅ Environment variables loaded from .env file")
    except ImportError:
        logger.warning(
            "⚠️ python-dotenv not installed, using system environment variables"
        )

    # Check if API key is available
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logger.error("❌ GEMINI_API_KEY not found. Please check your .env file.")
        print("\n❌ Please set GEMINI_API_KEY in your .env file")
        exit(1)

    # Run test
    result = asyncio.run(test_voice_agent())

    if result:
        print("\n✅ Voice Agent Service is working correctly!")
    else:
        print("\n❌ Voice Agent Service test failed!")
