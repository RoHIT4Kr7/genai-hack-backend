import asyncio
from typing import Dict, Any, List
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from loguru import logger
from models.schemas import StoryInputs, GeneratedStory
from services.story_service import story_service

# Removed gemini_image_service - using nano_banana_service
from services.chirp3hd_audio_service import chirp3hd_audio_service as audio_service
from workflows.nano_banana_workflow_node import nano_banana_workflow_node
from services.gcs_storage_service import gcs_storage_service as storage_service
from utils.helpers import validate_story_consistency


# State is a plain dict to satisfy LangGraph expectations


async def story_planning_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Generate the complete 6-panel story plan."""
    try:
        logger.info(f"Starting story planning for {state['story_id']}")

        # Generate story plan using Mangaka-Sensei
        panels = await story_service.generate_story_plan(state["inputs"])
        state["panels"] = panels
        state["status"] = "story_planned"

        logger.info(f"Story planning completed for {state['story_id']}")
        return state

    except Exception as e:
        logger.error(f"Story planning failed for {state.get('story_id')}: {e}")
        state["error"] = f"Story planning failed: {str(e)}"
        state["status"] = "error"
        return state


async def story_consistency_validator_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Validate character consistency across panels."""
    try:
        logger.info(f"Validating story consistency for {state['story_id']}")

        if not state.get("panels"):
            raise Exception("No panels to validate")

        # Validate consistency
        is_consistent = validate_story_consistency(state["panels"])

        if not is_consistent:
            logger.warning(
                f"Story consistency validation failed for {state['story_id']}"
            )
            # Regenerate story plan
            state["panels"] = await story_service.generate_story_plan(state["inputs"])

            # Validate again
            is_consistent = validate_story_consistency(state["panels"])
            if not is_consistent:
                raise Exception(
                    "Story consistency validation failed after regeneration"
                )

        state["status"] = "validated"
        logger.info(f"Story consistency validated for {state['story_id']}")
        return state

    except Exception as e:
        logger.error(
            f"Story consistency validation failed for {state.get('story_id')}: {e}"
        )
        state["error"] = f"Consistency validation failed: {str(e)}"
        state["status"] = "error"
        return state


async def image_generation_loop_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Generate images for all 6 panels using Imagen 4.0."""
    try:
        logger.info(f"Starting Imagen 4.0 image generation for {state['story_id']}")

        if not state.get("panels"):
            raise Exception("No panels available for image generation")

        # Generate all panel images using nano-banana
        from services.nano_banana_service import nano_banana_service

        image_urls = await nano_banana_service.generate_panel_images_parallel(
            state["panels"], state["story_id"]
        )
        state["image_urls"] = image_urls
        state["status"] = "images_generated"

        logger.info(
            f"Imagen 4.0 image generation completed for {state['story_id']}: {len(image_urls)} images"
        )
        return state

    except Exception as e:
        logger.error(f"Image generation failed for {state.get('story_id')}: {e}")
        state["error"] = f"Image generation failed: {str(e)}"
        state["status"] = "error"
        return state


async def nano_banana_reference_generation_node(
    state: Dict[str, Any],
) -> Dict[str, Any]:
    """Generate reference images using nano-banana for character consistency."""
    return await nano_banana_workflow_node.generate_reference_images_node(state)


async def nano_banana_image_generation_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Generate all 6 panels using nano-banana with reference consistency."""
    try:
        return await nano_banana_workflow_node.generate_panels_with_nano_banana_node(
            state
        )
    except Exception as e:
        logger.error(f"Image generation failed for {state.get('story_id')}: {e}")
        state["error"] = f"Image generation failed: {str(e)}"
        state["status"] = "error"
        return state


async def audio_generation_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Generate background music and TTS for all panels."""
    try:
        logger.info(f"Starting audio generation for {state['story_id']}")

        if not state.get("panels"):
            raise Exception("No panels available for audio generation")

        # Generate background music and TTS for all panels
        background_urls, tts_urls = await audio_service.generate_all_audio(
            state["panels"], state["story_id"]
        )
        state["background_urls"] = background_urls
        state["tts_urls"] = tts_urls
        state["status"] = "audio_generated"

        logger.info(f"Audio generation completed for {state['story_id']}")
        return state

    except Exception as e:
        logger.error(f"Audio generation failed for {state.get('story_id')}: {e}")
        state["error"] = f"Audio generation failed: {str(e)}"
        state["status"] = "error"
        return state


async def final_assembly_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Assemble the final story with all assets."""
    try:
        logger.info(f"Starting final assembly for {state['story_id']}")

        # Create the final story object with separate audio URLs
        story = GeneratedStory(
            story_id=state["story_id"],
            panels=state["panels"],
            image_urls=state["image_urls"],
            audio_url="",  # No synchronized audio - separate background and TTS URLs available
            status="completed",
        )

        state["status"] = "completed"
        logger.info(f"Final assembly completed for {state['story_id']}")
        return state

    except Exception as e:
        logger.error(f"Final assembly failed for {state.get('story_id')}: {e}")
        state["error"] = f"Final assembly failed: {str(e)}"
        state["status"] = "error"
        return state


def create_nano_banana_manga_workflow() -> StateGraph:
    """
    Create a LangGraph workflow that uses nano-banana for images + Chirp 3 HD for audio.

    This is the enhanced workflow that integrates nano-banana (Gemini 2.5 Flash Image Preview)
    while keeping your existing Chirp 3 HD TTS system.
    """
    workflow = StateGraph(dict)

    # Add workflow nodes
    workflow.add_node("story_planning", story_planning_node)
    workflow.add_node("story_validation", story_consistency_validator_node)
    workflow.add_node(
        "nano_banana_reference_generation", nano_banana_reference_generation_node
    )
    workflow.add_node("nano_banana_image_generation", nano_banana_image_generation_node)
    workflow.add_node(
        "chirp3hd_audio_generation",
        nano_banana_workflow_node.generate_audio_with_chirp3hd_node,
    )
    workflow.add_node("final_assembly", final_assembly_node)

    # Define workflow edges
    workflow.set_entry_point("story_planning")
    workflow.add_edge("story_planning", "story_validation")
    workflow.add_edge("story_validation", "nano_banana_reference_generation")
    workflow.add_edge(
        "nano_banana_reference_generation", "nano_banana_image_generation"
    )
    workflow.add_edge("nano_banana_image_generation", "chirp3hd_audio_generation")
    workflow.add_edge("chirp3hd_audio_generation", "final_assembly")
    workflow.set_finish_point("final_assembly")

    logger.info("✅ Nano-banana + Chirp 3 HD manga workflow created")
    return workflow


def create_manga_workflow() -> StateGraph:
    """Create the LangGraph workflow for manga generation."""

    # Create the workflow graph
    workflow = StateGraph(dict)

    # Add nodes
    workflow.add_node("story_planning", story_planning_node)
    workflow.add_node("consistency_validator", story_consistency_validator_node)
    workflow.add_node("image_generation", image_generation_loop_node)
    workflow.add_node("audio_generation", audio_generation_node)
    workflow.add_node("final_assembly", final_assembly_node)

    # Define the workflow flow
    workflow.set_entry_point("story_planning")

    # Conditional flows with error handling using add_conditional_edges
    workflow.add_conditional_edges(
        "story_planning",
        lambda s: "end" if s.get("status") == "error" else "consistency_validator",
        {
            "end": END,
            "consistency_validator": "consistency_validator",
        },
    )

    workflow.add_conditional_edges(
        "consistency_validator",
        lambda s: "end" if s.get("status") == "error" else "image_generation",
        {
            "end": END,
            "image_generation": "image_generation",
        },
    )

    workflow.add_conditional_edges(
        "image_generation",
        lambda s: "end" if s.get("status") == "error" else "audio_generation",
        {
            "end": END,
            "audio_generation": "audio_generation",
        },
    )

    workflow.add_conditional_edges(
        "audio_generation",
        lambda s: "end" if s.get("status") == "error" else "final_assembly",
        {
            "end": END,
            "final_assembly": "final_assembly",
        },
    )

    # End the workflow after final assembly
    workflow.add_edge("final_assembly", END)

    return workflow


class MangaWorkflowManager:
    def __init__(self, use_nano_banana: bool = False):
        """
        Initialize workflow manager.

        Args:
            use_nano_banana: If True, use nano-banana + Chirp 3 HD workflow.
                           If False, use original Imagen 4.0 + Chirp 3 HD workflow.
        """
        self.use_nano_banana = use_nano_banana

        if use_nano_banana:
            self.workflow = create_nano_banana_manga_workflow()
            logger.info("🎨 Using nano-banana + Chirp 3 HD workflow")
        else:
            self.workflow = create_manga_workflow()
            logger.info("🖼️ Using Nano-banana + Chirp 3 HD workflow")

        self.memory = MemorySaver()
        self.app = self.workflow.compile(checkpointer=self.memory)

    async def generate_story(self, inputs: StoryInputs) -> GeneratedStory:
        """Execute the complete manga generation workflow."""
        try:
            # Create initial state
            state: Dict[str, Any] = {
                "story_id": f"story_{asyncio.get_event_loop().time():.0f}",
                "inputs": inputs,
                "panels": [],
                "image_urls": [],
                "background_urls": [],
                "tts_urls": [],
                "status": "pending",
                "error": "",
                "created_at": asyncio.get_event_loop().time(),
            }

            logger.info(f"Starting manga workflow for {state['story_id']}")

            # Execute the workflow
            config = {"configurable": {"thread_id": state["story_id"]}}
            result: Dict[str, Any] = await self.app.ainvoke(state, config)

            # Check if workflow completed successfully
            if result.get("status") == "completed":
                # Create the final story object
                story = GeneratedStory(
                    story_id=result.get("story_id", ""),
                    panels=result.get("panels", []),
                    image_urls=result.get("image_urls", []),
                    audio_url="",  # No synchronized audio - separate background and TTS URLs available
                    status="completed",
                )

                logger.info(
                    f"Manga workflow completed successfully: {state['story_id']}"
                )
                return story
            else:
                raise Exception(
                    f"Workflow failed with status: {result.get('status')}, error: {result.get('error')}"
                )

        except Exception as e:
            logger.error(f"Manga workflow failed: {e}")
            raise

    async def get_workflow_status(self, story_id: str) -> Dict[str, Any]:
        """Get the status of a workflow execution."""
        try:
            # Get the checkpoint from memory
            config = {"configurable": {"thread_id": story_id}}
            checkpoint = await self.memory.aget(config)

            if checkpoint:
                return {
                    "story_id": story_id,
                    "status": checkpoint.get("status", "unknown"),
                    "error": checkpoint.get("error", ""),
                    "created_at": checkpoint.get("created_at", ""),
                }
            else:
                return {
                    "story_id": story_id,
                    "status": "not_found",
                    "error": "Workflow not found",
                }

        except Exception as e:
            logger.error(f"Failed to get workflow status for {story_id}: {e}")
            return {"story_id": story_id, "status": "error", "error": str(e)}


# Global workflow manager instance
workflow_manager = MangaWorkflowManager()
