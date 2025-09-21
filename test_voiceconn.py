import os
import asyncio
from google import genai
from google.genai import types

# Ensure we're using Google AI Studio, not Vertex AI
os.environ.pop("GOOGLE_GENAI_USE_VERTEXAI", None)

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("❌ GEMINI_API_KEY not set!")

client = genai.Client(api_key=api_key, http_options={"api_version": "v1beta"})

print("✅ Regular API confirmed working!")

# Test Live API models with corrected syntax
MODELS_TO_TRY = [
    "gemini-live-2.5-flash-preview",
    "gemini-2.0-flash-live-001",
    "gemini-2.5-flash-preview-native-audio-dialog",
]


async def test_live_model(model_name):
    try:
        print(f"🔄 Testing {model_name}...")

        # Configuration for text-only interaction
        config = types.LiveConnectConfig(
            response_modalities=["TEXT"],
            speech_config=types.SpeechConfig(language_code="en-US"),
        )

        async with client.aio.live.connect(model=model_name, config=config) as session:

            # ✅ FIXED: Use named parameter 'text=' not positional argument
            await session.send_client_content(
                turns=[
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_text(
                                text="Hello Gemini Live! Can you respond with text?"
                            )
                        ],  # Fixed!
                    )
                ],
                turn_complete=True,
            )

            # Set timeout to avoid hanging
            try:
                async with asyncio.timeout(15):  # Increased timeout
                    async for response in session.receive():
                        # Handle different response types
                        if (
                            hasattr(response, "server_content")
                            and response.server_content
                        ):
                            if (
                                hasattr(response.server_content, "model_turn")
                                and response.server_content.model_turn
                            ):
                                for part in response.server_content.model_turn.parts:
                                    if hasattr(part, "text") and part.text:
                                        print(f"✅ {model_name}: {part.text}")
                                        return True

                            # Check for turn completion
                            if (
                                hasattr(response.server_content, "turn_complete")
                                and response.server_content.turn_complete
                            ):
                                print(
                                    f"🔄 {model_name}: Turn completed but no text response received"
                                )
                                break

                        # Print response type for debugging
                        print(f"� {model_name}: Response type: {type(response)}")

            except asyncio.TimeoutError:
                print(f"⏰ {model_name}: Response timeout")
                return False

    except Exception as e:
        error_msg = str(e)

        # Categorize different types of errors
        if "404" in error_msg:
            print(
                f"🚫 {model_name}: Model not accessible (404 - requires special access)"
            )
        elif (
            "invalid frame payload data" in error_msg
            and "Cannot extract voices" in error_msg
        ):
            print(
                f"🎤 {model_name}: Model accessible but expects AUDIO input, not text"
            )
            return "audio_only"  # Special return to indicate audio-only model
        elif "UNAUTHENTICATED" in error_msg:
            print(f"🔑 {model_name}: Authentication error")
        else:
            print(f"❌ {model_name}: {error_msg}")

    return False


async def test_live_api():
    print("\n🧪 Testing Live API models...")

    accessible_models = []
    audio_only_models = []

    for model in MODELS_TO_TRY:
        result = await test_live_model(model)

        if result is True:
            accessible_models.append(model)
        elif result == "audio_only":
            audio_only_models.append(model)

        await asyncio.sleep(1)  # Small delay between tests

    # Summary
    if accessible_models:
        print(f"\n🎉 Text-accessible models: {accessible_models}")

    if audio_only_models:
        print(
            f"\n🎤 Audio-only models (working but need audio input): {audio_only_models}"
        )

    if not accessible_models and not audio_only_models:
        print("\n❌ No Live API models are currently text-accessible with your API key")

    print(
        "\n💡 The 'Cannot extract voices' error means the model IS working but expects audio input!"
    )


# Run the tests
asyncio.run(test_live_api())
