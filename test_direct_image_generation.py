#!/usr/bin/env python3
"""
Direct test of nano_banana_workflow_node image generation
"""
import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from workflows.nano_banana_workflow_node import nano_banana_workflow_node
from services.gcs_storage_service import gcs_storage_service


async def test_direct_image_generation():
    """Test direct image generation using nano_banana_workflow_node"""
    print("🧪 Testing Direct Image Generation")
    print("=" * 50)

    # Create a test panel prompt
    test_prompt = """
    Create a Studio Ghibli style manga panel showing a young woman with short brown hair 
    sitting peacefully in a forest clearing, surrounded by gentle spirits of nature. 
    The scene should convey tranquility and inner peace. Style should be soft, 
    hand-drawn anime art like Studio Ghibli films.
    """

    try:
        print("📡 Making direct API call to GenAI SDK...")

        # Test direct API call using the same method as the workflow node
        import google.genai as genai
        from config.settings import settings

        client = genai.Client(api_key=settings.gemini_api_key)

        response = await asyncio.to_thread(
            client.models.generate_content,
            model="gemini-2.5-flash-image-preview",
            contents=[test_prompt],
        )

        print(f"✅ Response received: {type(response)}")

        # Use the workflow node's extraction method
        image_data = nano_banana_workflow_node._extract_image_from_response(response)

        if len(image_data) < 1000:  # Likely placeholder if very small
            print(f"⚠️  Image data is very small: {len(image_data)} bytes")
            print("🔍 This might be a placeholder image")
            return False
        else:
            print(f"✅ Image data extracted: {len(image_data)} bytes")

            # Upload to test if it's a real image
            test_url = await gcs_storage_service.upload_bytes(
                image_data, "test/direct_generation_test.png"
            )

            print(f"🌐 Test image uploaded: {test_url}")
            print("✅ Real image generation working!")
            return True

    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    result = asyncio.run(test_direct_image_generation())

    if result:
        print("\n🎯 CONCLUSION: Image generation is working correctly")
        print("   Problem might be in workflow integration or data flow")
    else:
        print("\n🚨 CONCLUSION: Image generation is still broken")
        print("   Need to fix the GenAI SDK integration")
