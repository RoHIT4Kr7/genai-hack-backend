import asyncio
from typing import Dict, List, Any, Optional, Tuple
from loguru import logger
from concurrent.futures import ThreadPoolExecutor

from services.image_service import image_service
from services.audio_service import audio_service
from services.storage_service import storage_service

# Removed streaming_music_service dependency
from utils.helpers import create_structured_image_prompt, generate_panel_prompt


class PanelProcessor:
    """
    Processes individual panels to generate images, audio, and music immediately.

    This class handles the parallel processing of panel assets as soon as
    a complete panel becomes available from the streaming parser, using
    streaming music for continuous adaptation.
    """

    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=10)  # For CPU-bound tasks
        self.active_tasks = {}  # Track active processing tasks
        self.story_context = {}  # Store story context for music prompts
        self.user_age = 16  # Default user age for TTS
        self.user_gender = "non-binary"  # Default user gender for TTS

    async def process_panel(
        self,
        panel_data: Dict[str, Any],
        story_id: str,
        emit_progress,
        story_seed: int = None,
    ) -> Dict[str, Any]:
        """
        Process a single panel to generate all assets (image, music, TTS).

        Uses dynamic prompt generation for personalized music.

        Args:
            panel_data: Complete panel data from streaming parser
            story_id: Story ID for asset storage
            emit_progress: Function to emit progress updates
            story_seed: Random seed for consistent character design across panels

        Returns:
            Panel data with generated asset URLs
        """
        panel_number = panel_data["panel_number"]
        logger.info(f"🎨 Starting processing for panel {panel_number}")

        try:
            # Emit panel processing start
            logger.info(f"📡 Emitting panel_processing_start for panel {panel_number}")
            try:
                await asyncio.wait_for(
                    emit_progress(
                        event_type="panel_processing_start",
                        data={"panel_number": panel_number, "story_id": story_id},
                    ),
                    timeout=5.0,  # 5 second timeout for socket emission
                )
                logger.info(
                    f"✅ Emitted panel_processing_start for panel {panel_number}"
                )
            except asyncio.TimeoutError:
                logger.error(f"⏰ Socket emission timed out for panel {panel_number}")
            except Exception as e:
                logger.error(f"❌ Socket emission failed for panel {panel_number}: {e}")

            # Skip music generation - use static background music
            music_url = (
                "/src/assets/audio/background-music.mp3"  # Static background music
            )

            # Generate image and TTS in parallel
            logger.info(f"🖼️ Starting image and TTS generation for panel {panel_number}")
            tasks = {
                "image": self._generate_panel_image(
                    panel_data, story_id, emit_progress, story_seed
                ),
                "tts": self._generate_panel_tts(panel_data, story_id, emit_progress),
            }
            logger.info(f"📋 Created {len(tasks)} tasks for panel {panel_number}")

            # Wait for image and TTS to complete with timeout
            logger.info(
                f"⏳ Waiting for image and TTS generation for panel {panel_number}"
            )
            try:
                results = await asyncio.wait_for(
                    asyncio.gather(*tasks.values(), return_exceptions=True),
                    timeout=90.0,  # 1.5 minute timeout for asset generation (optimized)
                )
                logger.info(f"✅ Asset generation completed for panel {panel_number}")
            except asyncio.TimeoutError:
                logger.error(f"⏰ Asset generation timed out for panel {panel_number}")
                results = [Exception("Timeout") for _ in tasks]

            # Process results and handle any errors with better fallbacks
            processed_panel = panel_data.copy()
            asset_urls = {"music": music_url}

            for i, (task_name, result) in enumerate(zip(tasks.keys(), results)):
                if isinstance(result, Exception):
                    logger.error(
                        f"Panel {panel_number} {task_name} generation failed: {result}"
                    )
                    # Provide better fallback URLs
                    if task_name == "image":
                        asset_urls[task_name] = (
                            ""  # Frontend will handle fallback image
                        )
                    elif task_name == "tts":
                        asset_urls[task_name] = ""  # Frontend will handle fallback TTS
                    else:
                        asset_urls[task_name] = ""

                    # Emit specific error event
                    await emit_progress(
                        event_type=f"{task_name}_generation_failed",
                        data={
                            "panel_number": panel_number,
                            "story_id": story_id,
                            "error": str(result),
                            "fallback_used": True,
                        },
                    )
                else:
                    asset_urls[task_name] = result

            # Update panel data with asset URLs
            processed_panel.update(
                {
                    "image_url": asset_urls["image"],
                    "music_url": asset_urls["music"],
                    "tts_url": asset_urls["tts"],
                }
            )

            # Emit panel processing completion
            await emit_progress(
                event_type="panel_processing_complete",
                data={
                    "panel_number": panel_number,
                    "story_id": story_id,
                    "panel_data": processed_panel,
                    "asset_urls": asset_urls,
                },
            )

            # Also emit a panel_update event for frontend to add/update panels dynamically
            await emit_progress(
                event_type="panel_update",
                data={
                    "panel_number": panel_number,
                    "story_id": story_id,
                    "panel_data": processed_panel,
                },
            )

            logger.info(f"Panel {panel_number} processing completed")
            return processed_panel

        except Exception as e:
            logger.error(f"Error processing panel {panel_number}: {e}")

            # Emit error event
            await emit_progress(
                event_type="panel_processing_error",
                data={
                    "panel_number": panel_number,
                    "story_id": story_id,
                    "error": str(e),
                },
            )

            # Return panel with empty asset URLs
            panel_data.update({"image_url": "", "music_url": "", "tts_url": ""})
            return panel_data

    async def _generate_panel_image(
        self,
        panel_data: Dict[str, Any],
        story_id: str,
        emit_progress,
        story_seed: int = None,
    ) -> str:
        """Generate image for a panel."""
        panel_number = panel_data["panel_number"]

        try:
            logger.info(f"Generating image for panel {panel_number}")

            # Emit image generation start
            await emit_progress(
                event_type="image_generation_start",
                data={"panel_number": panel_number, "story_id": story_id},
            )

            # Create structured image prompt using the new panel-specific function
            structured_prompt = generate_panel_prompt(panel_number, panel_data)

            # Generate and upload image
            image_url = await image_service.generate_single_panel(
                structured_prompt, story_id, panel_number, story_seed
            )

            # Emit image generation completion
            await emit_progress(
                event_type="image_generation_complete",
                data={
                    "panel_number": panel_number,
                    "story_id": story_id,
                    "image_url": image_url,
                },
            )

            logger.info(f"Image generated for panel {panel_number}: {image_url}")
            return image_url

        except Exception as e:
            logger.error(f"Image generation failed for panel {panel_number}: {e}")

            # Check if it's a quota exceeded error
            error_str = str(e).lower()
            is_quota_exceeded = "quota exceeded" in error_str or "429" in error_str

            if is_quota_exceeded:
                logger.warning(
                    f"Quota exceeded for panel {panel_number}, trying fallback image generation"
                )
                try:
                    # Try fallback image generation
                    fallback_image_data = await image_service.generate_fallback_image(
                        panel_number, story_seed
                    )
                    fallback_image_url = await storage_service.upload_image(
                        fallback_image_data, story_id, panel_number
                    )

                    # Emit fallback image generation completion
                    await emit_progress(
                        event_type="image_generation_complete",
                        data={
                            "panel_number": panel_number,
                            "story_id": story_id,
                            "image_url": fallback_image_url,
                            "is_fallback": True,
                        },
                    )

                    logger.info(
                        f"Fallback image generated for panel {panel_number}: {fallback_image_url}"
                    )
                    return fallback_image_url

                except Exception as fallback_error:
                    logger.error(
                        f"Fallback image generation also failed for panel {panel_number}: {fallback_error}"
                    )

            # Emit error
            await emit_progress(
                event_type="image_generation_error",
                data={
                    "panel_number": panel_number,
                    "story_id": story_id,
                    "error": str(e),
                },
            )
            raise

    async def _generate_panel_tts(
        self, panel_data: Dict[str, Any], story_id: str, emit_progress
    ) -> str:
        """Generate TTS audio for a panel."""
        panel_number = panel_data["panel_number"]

        try:
            logger.info(f"Generating TTS for panel {panel_number}")

            # Emit TTS generation start
            await emit_progress(
                event_type="tts_generation_start",
                data={"panel_number": panel_number, "story_id": story_id},
            )

            # Get TTS text (use dialogue_text as default)
            tts_text = panel_data.get(
                "tts_text",
                panel_data.get("dialogue_text", f"Panel {panel_number} narration"),
            )

            # Generate TTS audio using user preferences
            tts_data = await audio_service.generate_tts_audio(
                tts_text, panel_number, self.user_age, self.user_gender
            )

            # Upload TTS audio
            tts_url = await storage_service.upload_tts_audio(
                tts_data, story_id, panel_number
            )

            # Emit TTS generation completion
            await emit_progress(
                event_type="tts_generation_complete",
                data={
                    "panel_number": panel_number,
                    "story_id": story_id,
                    "tts_url": tts_url,
                },
            )

            logger.info(f"TTS generated for panel {panel_number}: {tts_url}")
            return tts_url

        except Exception as e:
            logger.error(f"TTS generation failed for panel {panel_number}: {e}")

            # Emit error
            await emit_progress(
                event_type="tts_generation_error",
                data={
                    "panel_number": panel_number,
                    "story_id": story_id,
                    "error": str(e),
                },
            )
            raise

    def set_story_context(self, context: Dict[str, Any]):
        """Set the story context for dynamic music prompt generation."""
        self.story_context = context
        logger.info(f"Set story context: {list(context.keys())}")

    async def process_panels_parallel(
        self,
        panels: List[Dict[str, Any]],
        story_id: str,
        emit_progress,
        user_age: int = 16,
        user_gender: str = "non-binary",
        story_seed: int = None,
    ) -> List[Dict[str, Any]]:
        """
        Process all panels in parallel - generate all images first, then all audio.

        Args:
            panels: List of all panel data
            story_id: Story ID for asset storage
            emit_progress: Function to emit progress updates
            user_age: User age for voice selection
            user_gender: User gender for voice selection
            story_seed: Random seed for consistent character design

        Returns:
            List of processed panels with asset URLs
        """
        try:
            # Set user preferences for TTS
            self.user_age = user_age
            self.user_gender = user_gender

            logger.info(f"Starting parallel processing for {len(panels)} panels")

            # Emit parallel processing start
            await emit_progress(
                event_type="parallel_processing_start",
                data={"story_id": story_id, "total_panels": len(panels)},
            )

            # Step 1: Generate all images in parallel
            logger.info("Generating all images in parallel")
            await emit_progress(
                event_type="parallel_image_generation_start",
                data={"story_id": story_id, "total_panels": len(panels)},
            )

            image_tasks = []
            for panel in panels:
                image_tasks.append(
                    self._generate_panel_image(
                        panel, story_id, emit_progress, story_seed
                    )
                )

            # Wait for all images to complete
            image_results = await asyncio.gather(*image_tasks, return_exceptions=True)
            image_urls = []

            for i, result in enumerate(image_results):
                if isinstance(result, Exception):
                    logger.error(f"Image generation failed for panel {i+1}: {result}")
                    image_urls.append("")
                else:
                    image_urls.append(result)

            await emit_progress(
                event_type="parallel_image_generation_complete",
                data={"story_id": story_id, "image_urls": image_urls},
            )

            # Step 2: Generate all TTS audio in parallel
            logger.info("Generating all TTS audio in parallel")
            await emit_progress(
                event_type="parallel_tts_generation_start",
                data={"story_id": story_id, "total_panels": len(panels)},
            )

            tts_tasks = []
            for panel in panels:
                tts_tasks.append(
                    self._generate_panel_tts(panel, story_id, emit_progress)
                )

            # Wait for all TTS to complete
            tts_results = await asyncio.gather(*tts_tasks, return_exceptions=True)
            tts_urls = []

            for i, result in enumerate(tts_results):
                if isinstance(result, Exception):
                    logger.error(f"TTS generation failed for panel {i+1}: {result}")
                    tts_urls.append("")
                else:
                    tts_urls.append(result)

            await emit_progress(
                event_type="parallel_tts_generation_complete",
                data={"story_id": story_id, "tts_urls": tts_urls},
            )

            # Step 3: Combine results into processed panels
            processed_panels = []
            music_url = (
                "/src/assets/audio/background-music.mp3"  # Static background music
            )

            for i, panel in enumerate(panels):
                processed_panel = panel.copy()
                processed_panel.update(
                    {
                        "image_url": image_urls[i] if i < len(image_urls) else "",
                        "music_url": music_url,
                        "tts_url": tts_urls[i] if i < len(tts_urls) else "",
                    }
                )
                processed_panels.append(processed_panel)

                # Emit individual panel completion for slideshow
                await emit_progress(
                    event_type="panel_update",
                    data={
                        "panel_number": panel["panel_number"],
                        "story_id": story_id,
                        "panel_data": processed_panel,
                    },
                )

            # Emit parallel processing completion
            await emit_progress(
                event_type="parallel_processing_complete",
                data={"story_id": story_id, "total_panels": len(processed_panels)},
            )

            # Emit slideshow ready event - all assets are now available
            await emit_progress(
                event_type="slideshow_ready",
                data={
                    "story_id": story_id,
                    "total_panels": len(processed_panels),
                    "message": "All images and audio assets are ready. Slideshow can now start.",
                },
            )

            logger.info(
                f"Parallel processing completed for {len(processed_panels)} panels - slideshow ready"
            )
            return processed_panels

        except Exception as e:
            logger.error(f"Error in parallel panel processing: {e}")

            # Emit error event
            await emit_progress(
                event_type="parallel_processing_error",
                data={"story_id": story_id, "error": str(e)},
            )
            raise

    async def process_panels_streaming(
        self,
        panels_stream,
        story_id: str,
        emit_progress,
        user_age: int = 16,
        user_gender: str = "non-binary",
    ) -> List[Dict[str, Any]]:
        """
        Process panels as they come from the streaming generator.

        Args:
            panels_stream: Async generator yielding panel data
            story_id: Story ID for asset storage
            emit_progress: Function to emit progress updates
            user_age: User age for voice selection
            user_gender: User gender for voice selection

        Returns:
            List of processed panels with asset URLs
        """
        processed_panels = []

        try:
            # Process panels as they come from the stream
            async for panel_data in panels_stream:
                # Update user age and gender in the panel processor for TTS
                self.user_age = user_age
                self.user_gender = user_gender

                # Start processing this panel immediately
                processing_task = self.process_panel(
                    panel_data, story_id, emit_progress
                )

                # Wait for this specific panel to complete before moving to next
                try:
                    processed_panel = await processing_task
                    processed_panels.append(processed_panel)

                except Exception as e:
                    logger.error(
                        f"Panel {panel_data['panel_number']} processing failed: {e}"
                    )
                    # Add panel with empty assets
                    panel_data.update({"image_url": "", "music_url": "", "tts_url": ""})
                    processed_panels.append(panel_data)

            logger.info(
                f"Processed {len(processed_panels)} panels for story {story_id}"
            )
            return processed_panels

        except Exception as e:
            logger.error(f"Error in streaming panel processing: {e}")

            # Emit error event
            await emit_progress(
                event_type="panel_processing_stream_error",
                data={"story_id": story_id, "error": str(e)},
            )
            raise


# Global panel processor instance
panel_processor = PanelProcessor()
