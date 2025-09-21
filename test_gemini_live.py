#!/usr/bin/env python3
"""
Test Gemini Live API connection directly
"""

import asyncio
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load environment variables
load_dotenv()

async def test_gemini_live():
    """Test the Gemini Live API connection"""
    print("🔍 Testing Gemini Live API connection...")
    
    # Get API key
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not found")
        return False
        
    print(f"✅ API Key loaded: {api_key[:10]}...{api_key[-4:]}")
    
    # Initialize client
    try:
        client = genai.Client(
            http_options={"api_version": "v1beta"},
            api_key=api_key,
        )
        print("✅ Gemini client initialized")
    except Exception as e:
        print(f"❌ Failed to initialize client: {e}")
        return False
    
    # Test minimal config
    print("🧪 Testing minimal LiveConnectConfig...")
    minimal_config = types.LiveConnectConfig(
        response_modalities=["AUDIO"],
    )
    
    print(f"Config: {minimal_config}")
    
    # Test connection with different models
    models_to_try = [
        "models/gemini-2.5-flash-live-preview",
        "models/gemini-live-2.5-flash-preview",
        "models/gemini-2.0-flash-live-001"
    ]
    
    for model_name in models_to_try:
        try:
            print(f"🔗 Attempting to connect with model: {model_name}")
            session_context = client.aio.live.connect(
                model=model_name,
                # config=minimal_config,  # Try without config first
            )
        
        print("⏳ Waiting for session to establish...")
        session = await asyncio.wait_for(
            session_context.__aenter__(), timeout=30.0
        )
        
        print("✅ Successfully connected to Gemini Live API!")
        
        # Test sending a simple message
        print("📝 Testing text message...")
        await session.send(input="Hello, can you hear me?", end_of_turn=True)
        print("✅ Message sent successfully")
        
        # Try to receive a response
        print("👂 Listening for response...")
        try:
            turn = session.receive()
            async for response in turn:
                if hasattr(response, "text") and response.text:
                    print(f"🤖 AI Response: {response.text}")
                    break
            else:
                print("⚠️  No text response received")
        except Exception as e:
            print(f"⚠️  Error receiving response: {e}")
        
        # Clean up
        await session_context.__aexit__(None, None, None)
        print("✅ Session closed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        print(f"❌ Error type: {type(e).__name__}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_gemini_live())
    if result:
        print("\n🎉 Test completed successfully!")
    else:
        print("\n💥 Test failed!")