#!/usr/bin/env python3
"""
Simple WebSocket test for voice agent
"""

import asyncio
import websockets
import json
from datetime import datetime


async def test_voice_websocket():
    """Test the voice WebSocket endpoint"""
    session_id = f"test_session_{int(datetime.now().timestamp())}"
    uri = f"ws://localhost:8000/api/v1/voice/ws/{session_id}"

    print(f"🔗 Connecting to: {uri}")

    try:
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connected!")

            # Wait for initial messages
            try:
                # Receive initial connection confirmation
                message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                data = json.loads(message)
                print(f"📥 Received: {data}")

                if (
                    data.get("type") == "session_status"
                    and data.get("status") == "connected"
                ):
                    print("✅ Session connected successfully!")

                    # Send a test text message
                    test_message = {
                        "type": "text_message",
                        "session_id": session_id,
                        "message": "Hello! Can you help me create an anime character?",
                    }

                    print(f"📤 Sending test message: {test_message['message']}")
                    await websocket.send(json.dumps(test_message))

                    # Wait for responses
                    timeout_count = 0
                    max_timeouts = 10

                    while timeout_count < max_timeouts:
                        try:
                            response = await asyncio.wait_for(
                                websocket.recv(), timeout=2.0
                            )
                            response_data = json.loads(response)
                            print(f"📥 Response: {response_data}")

                            if response_data.get("type") == "ai_response":
                                print(
                                    f"🤖 AI said: {response_data.get('text', 'No text')}"
                                )
                                break
                            elif response_data.get("type") == "error":
                                print(
                                    f"❌ Error: {response_data.get('message', 'Unknown error')}"
                                )
                                break

                        except asyncio.TimeoutError:
                            timeout_count += 1
                            print(
                                f"⏰ Waiting for response... ({timeout_count}/{max_timeouts})"
                            )
                            continue

                    if timeout_count >= max_timeouts:
                        print("⏰ Timeout waiting for AI response")

                else:
                    print(f"❌ Unexpected initial message: {data}")

            except asyncio.TimeoutError:
                print("❌ Timeout waiting for initial connection confirmation")

    except websockets.exceptions.ConnectionClosed as e:
        print(f"🔌 Connection closed: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    print("🎤 Testing Voice Agent WebSocket Connection")
    print("=" * 50)
    asyncio.run(test_voice_websocket())
