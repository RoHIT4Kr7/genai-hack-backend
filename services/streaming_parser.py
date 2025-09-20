import re
import json
from typing import Dict, List, Any, Optional, AsyncGenerator
from loguru import logger
from models.schemas import StoryInputs
from services.dialogue_extractor import dialogue_extractor


class StreamingPanelParser:
    """
    Parses streaming LLM output to extract panel data incrementally.

    This class accumulates tokens and detects when complete panels are available
    to trigger immediate processing.
    """

    def __init__(self):
        self.accumulated_text = ""
        self.current_panel = 1
        self.max_panels = 6
        self.completed_panels = []
        self.partial_panel_data = {}
        self.character_sheet = None
        self.prop_sheet = None
        self.style_guide = None

    def reset(self):
        """Reset the parser state."""
        self.accumulated_text = ""
        self.current_panel = 1
        self.completed_panels = []
        self.partial_panel_data = {}
        self.character_sheet = None
        self.prop_sheet = None
        self.style_guide = None

    def _extract_global_sections(self, text: str) -> bool:
        """Extract global sections (CHARACTER_SHEET, PROP_SHEET, STYLE_GUIDE) from text."""
        updated = False

        # Extract CHARACTER_SHEET
        if self.character_sheet is None:
            character_match = re.search(r"CHARACTER_SHEET:\s*({.*?})", text, re.DOTALL)
            if character_match:
                try:
                    self.character_sheet = json.loads(character_match.group(1))
                    updated = True
                    logger.info("Extracted CHARACTER_SHEET from streaming response")
                except json.JSONDecodeError:
                    pass  # Wait for more complete data

        # Extract PROP_SHEET
        if self.prop_sheet is None:
            prop_match = re.search(r"PROP_SHEET:\s*({.*?})", text, re.DOTALL)
            if prop_match:
                try:
                    self.prop_sheet = json.loads(prop_match.group(1))
                    updated = True
                    logger.info("Extracted PROP_SHEET from streaming response")
                except json.JSONDecodeError:
                    pass

        # Extract STYLE_GUIDE
        if self.style_guide is None:
            style_match = re.search(r"STYLE_GUIDE:\s*({.*?})", text, re.DOTALL)
            if style_match:
                try:
                    self.style_guide = json.loads(style_match.group(1))
                    updated = True
                    logger.info("Extracted STYLE_GUIDE from streaming response")
                except json.JSONDecodeError:
                    pass

        return updated

    def _extract_panel_data(
        self, text: str, panel_number: int
    ) -> Optional[Dict[str, Any]]:
        """Extract panel-specific data for a given panel number."""
        # Try multiple dialogue text patterns for robustness
        dialogue_patterns = [
            rf'PANEL_{panel_number}:\s*dialogue_text:\s*"([^"]*)"',  # With quotes
            rf"PANEL_{panel_number}:\s*dialogue_text:\s*([^\n]+)",  # Without quotes, until newline
            rf'PANEL_{panel_number}:[^:]*dialogue_text[:\s]*"([^"]*)"',  # Flexible format with quotes
            rf"PANEL_{panel_number}:[^:]*dialogue_text[:\s]*([^\n]+)",  # Flexible format without quotes
            rf"Panel\s*{panel_number}:\s*'([^']*)'",  # Panel X: 'content' format (single quotes)
            rf'Panel\s*{panel_number}:\s*"([^"]*)"',  # Panel X: "content" format (double quotes)
            rf"Panel\s*{panel_number}:\s*([^'\"]+(?:'[^']*'[^'\"]*)*)",  # Panel X: mixed content with quotes
        ]

        dialogue_text = None
        for pattern in dialogue_patterns:
            dialogue_match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if dialogue_match:
                dialogue_text = dialogue_match.group(1).strip()
                if (
                    dialogue_text and len(dialogue_text) > 10
                ):  # Ensure meaningful content
                    logger.info(
                        f"Panel {panel_number} dialogue extracted with pattern: {pattern[:50]}..."
                    )
                    break

        if dialogue_text:
            # Check if we have all required global data
            if not all([self.character_sheet, self.prop_sheet, self.style_guide]):
                logger.warning(
                    f"Panel {panel_number} found but missing global data, creating with partial data"
                )
                # Create minimal global data if missing
                self.character_sheet = self.character_sheet or {
                    "name": "Hero",
                    "age": "young",
                    "appearance": "determined character",
                }
                self.prop_sheet = self.prop_sheet or {
                    "items": ["hope"],
                    "environment": "inspiring setting",
                }
                self.style_guide = self.style_guide or {
                    "art_style": "shonen manga",
                    "visual_elements": ["emotional"],
                }

            # Determine emotional tone based on panel number
            emotional_tone = self._determine_emotional_tone(panel_number, dialogue_text)

            panel_data = {
                "panel_number": panel_number,
                "character_sheet": self.character_sheet,
                "prop_sheet": self.prop_sheet,
                "style_guide": self.style_guide,
                "dialogue_text": dialogue_text,
                "emotional_tone": emotional_tone,
                "image_prompt": "",  # Will be generated separately
                "music_prompt": "",  # Will be generated separately
                "tts_text": dialogue_text,  # Default to dialogue text
                "user_mood": "neutral",  # Default values - could be passed from inputs
                "user_vibe": "calm",
            }

            logger.info(
                f"Extracted complete panel {panel_number} data with {len(dialogue_text)} chars of dialogue"
            )
            return panel_data

        return None

    def _determine_emotional_tone(self, panel_number: int, dialogue: str) -> str:
        """Determine emotional tone based on panel number and dialogue."""
        emotional_arc = {
            1: "neutral",  # Introduction
            2: "tense",  # Challenge
            3: "contemplative",  # Reflection
            4: "hopeful",  # Discovery
            5: "determined",  # Transformation
            6: "uplifting",  # Resolution
        }
        return emotional_arc.get(panel_number, "neutral")

    async def process_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Process a new token from the streaming response.

        Returns a complete panel dictionary if one is ready for processing,
        or None if more tokens are needed.
        """
        self.accumulated_text += token

        # Try to extract global sections
        self._extract_global_sections(self.accumulated_text)

        # Try to extract the current panel
        panel_data = self._extract_panel_data(self.accumulated_text, self.current_panel)

        if panel_data:
            # Mark this panel as completed and move to next
            self.completed_panels.append(panel_data)
            self.current_panel += 1

            # Reset accumulated text to continue with next panels
            # Keep global sections but clear panel-specific content
            self._reset_for_next_panel()

            return panel_data

        return None

    def _reset_for_next_panel(self):
        """Reset parser state for the next panel while keeping global data."""
        # Keep global sections, clear accumulated text for next panel
        self.accumulated_text = ""
        self.partial_panel_data = {}

    async def process_streaming_response(
        self, response_stream
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Process a streaming response and yield complete panels as they become available.

        Args:
            response_stream: Async generator yielding chunks from LLM

        Yields:
            Complete panel dictionaries ready for processing
        """
        self.reset()
        accumulated_full_text = ""

        try:
            async for chunk in response_stream:
                # Extract content from chunk
                if hasattr(chunk, "content"):
                    token = chunk.content
                else:
                    token = str(chunk)

                accumulated_full_text += token

                # Process the token
                panel_data = await self.process_token(token)

                # If we got a complete panel, yield it
                if panel_data:
                    yield panel_data

                # Check if we've reached the maximum number of panels
                if self.current_panel > self.max_panels:
                    break

            # After processing all tokens, try to extract any missed panels
            if accumulated_full_text and len(self.completed_panels) < self.max_panels:
                logger.info(
                    "Attempting robust dialogue extraction from complete response"
                )
                await self._extract_remaining_panels_robust(accumulated_full_text)

                # Yield any additional panels found
                for panel in self.completed_panels[len(self.completed_panels) :]:
                    yield panel

        except Exception as e:
            logger.error(f"Error processing streaming response: {e}")
            raise

    async def _extract_remaining_panels_robust(self, full_text: str):
        """Extract any missed panels using robust dialogue extraction."""
        try:
            # Extract all panels using robust method
            extracted_dialogues = dialogue_extractor.extract_all_panels_robust(
                full_text
            )

            # Create panels for any missing ones
            for panel_num in range(1, self.max_panels + 1):
                if panel_num > len(self.completed_panels):
                    if panel_num in extracted_dialogues:
                        dialogue_text = extracted_dialogues[panel_num]
                    else:
                        # Use fallback
                        dialogue_text = f"Panel {panel_num}: The journey continues with determination and hope."

                    # Ensure we have global data
                    if not all(
                        [self.character_sheet, self.prop_sheet, self.style_guide]
                    ):
                        self.character_sheet = self.character_sheet or {
                            "name": "Hero",
                            "age": "young",
                        }
                        self.prop_sheet = self.prop_sheet or {
                            "items": ["hope"],
                            "environment": "inspiring",
                        }
                        self.style_guide = self.style_guide or {
                            "art_style": "shonen manga"
                        }

                    panel_data = {
                        "panel_number": panel_num,
                        "character_sheet": self.character_sheet,
                        "prop_sheet": self.prop_sheet,
                        "style_guide": self.style_guide,
                        "dialogue_text": dialogue_text,
                        "emotional_tone": self._determine_emotional_tone(
                            panel_num, dialogue_text
                        ),
                        "image_prompt": "",
                        "music_prompt": "",
                        "tts_text": dialogue_text,
                    }

                    self.completed_panels.append(panel_data)
                    logger.info(
                        f"Added missing panel {panel_num} with robust extraction"
                    )

        except Exception as e:
            logger.error(f"Error in robust panel extraction: {e}")

    def get_final_panels(self) -> List[Dict[str, Any]]:
        """Get all completed panels."""
        return self.completed_panels.copy()

    def is_complete(self) -> bool:
        """Check if all panels have been processed."""
        return len(self.completed_panels) >= self.max_panels


class StreamingStoryGenerator:
    """
    Orchestrates the streaming story generation process.
    """

    def __init__(self, story_service):
        self.story_service = story_service
        self.parser = StreamingPanelParser()

    async def generate_streaming_story(
        self, inputs: StoryInputs, emit_progress
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Generate story panels using streaming LLM response.

        Args:
            inputs: Story generation inputs
            emit_progress: Function to emit progress updates

        Returns:
            List of complete panel dictionaries
        """
        try:
            logger.info("Starting streaming story generation")

            # Create the input context for the Story Architect AI
            input_context = f"""
            User Inputs:
            - Mood: {inputs.mood}
            - Vibe: {inputs.vibe}
            - Archetype: {inputs.archetype}
            - Dream: {inputs.dream}
            - Manga Title: {inputs.mangaTitle}
            - Nickname: {inputs.nickname}
            - Hobby: {inputs.hobby}
            - Age: {inputs.age}
            - Gender: {inputs.gender}

            Please create a complete 6-panel manga story structure following the Story Architect guidelines.
            """

            # 🚨 CRITICAL FIX: Properly format the template with user context
            from utils.helpers import STORY_ARCHITECT_PROMPT

            full_prompt = STORY_ARCHITECT_PROMPT.format(user_context=input_context)

            logger.info("Starting streaming LLM call")

            # Use astream for streaming response
            response_stream = self.story_service.llm.astream(full_prompt)

            # Process streaming response
            panel_count = 0
            async for chunk in response_stream:
                # Extract content from chunk
                if hasattr(chunk, "content"):
                    token = chunk.content
                else:
                    token = str(chunk)

                # Process the token
                panel_data = await self.parser.process_token(token)

                if panel_data:
                    panel_count += 1

                    # Emit progress update
                    await emit_progress(
                        event_type="panel_ready",
                        data={
                            "panel_number": panel_data["panel_number"],
                            "panel_data": panel_data,
                            "total_panels": panel_count,
                        },
                    )

                    logger.info(
                        f"Panel {panel_data['panel_number']} ready for processing"
                    )
                    yield panel_data

            # Check if we have all panels
            if panel_count < self.parser.max_panels:
                logger.warning(
                    f"Only got {panel_count} panels, expected {self.parser.max_panels}"
                )

                # Try to extract missed panels using enhanced dialogue extraction
                accumulated_text = getattr(self.parser, "accumulated_text", "")
                if accumulated_text:
                    logger.info(
                        "Attempting enhanced dialogue extraction for missing panels"
                    )
                    enhanced_dialogues = (
                        dialogue_extractor.validate_and_enhance_dialogue(
                            dialogue_extractor.extract_all_panels_robust(
                                accumulated_text
                            ),
                            inputs,
                        )
                    )

                    # Add missing panels with enhanced content
                    while panel_count < self.parser.max_panels:
                        panel_num = panel_count + 1
                        dialogue_text = enhanced_dialogues.get(
                            panel_num,
                            f"Panel {panel_num}: The journey continues with determination and hope.",
                        )

                        fallback_panel = self._create_fallback_panel(panel_num, inputs)
                        fallback_panel["dialogue_text"] = dialogue_text
                        fallback_panel["tts_text"] = dialogue_text

                        panel_count += 1
                        yield fallback_panel
                else:
                    # Use standard fallback panels
                    while panel_count < self.parser.max_panels:
                        fallback_panel = self._create_fallback_panel(
                            panel_count + 1, inputs
                        )
                        panel_count += 1
                        yield fallback_panel

            logger.info(
                f"Streaming story generation completed with {panel_count} panels"
            )

        except Exception as e:
            logger.error(f"Error in streaming story generation: {e}")
            # Yield fallback panels
            for i in range(self.parser.max_panels):
                yield self._create_fallback_panel(i + 1, inputs)

    def _create_fallback_panel(
        self, panel_number: int, inputs: StoryInputs
    ) -> Dict[str, Any]:
        """Create a fallback panel when streaming fails."""
        from utils.helpers import get_anime_style_by_mood

        manga_style = (
            get_anime_style_by_mood(inputs.mood, inputs.vibe)
            if inputs
            else "A beautiful and expressive anime style with clean lines and emotional depth."
        )

        # Create meaningful dialogue content based on emotional arc
        dialogue_content = self._generate_meaningful_dialogue(panel_number, inputs)

        return {
            "panel_number": panel_number,
            "character_sheet": {
                "name": inputs.nickname if inputs else "Hero",
                "age": str(inputs.age) if inputs else "young",
                "appearance": f"determined {inputs.gender if inputs else 'person'} with expressive eyes",
                "clothing": "modern casual outfit",
                "personality": "determined and hopeful",
                "goals": inputs.dream if inputs else "overcome challenges",
                "fears": f'struggles with {inputs.mood if inputs else "uncertainty"}',
                "strengths": "inner resilience and creativity",
            },
            "prop_sheet": {
                "items": [inputs.hobby if inputs else "symbolic item"],
                "environment": f'{inputs.vibe if inputs else "inspiring"} setting',
                "lighting": "dynamic lighting",
                "mood_elements": [inputs.vibe if inputs else "hope", "determination"],
            },
            "style_guide": {
                "art_style": manga_style,
                "visual_elements": ["dynamic composition", "emotional expression"],
                "framing": "cinematic manga panel composition",
                "details": "strong ink lines, detailed cross-hatching",
            },
            "dialogue_text": dialogue_content,
            "emotional_tone": {
                1: "neutral",
                2: "tense",
                3: "contemplative",
                4: "hopeful",
                5: "determined",
                6: "uplifting",
            }.get(panel_number, "neutral"),
            "image_prompt": f"Manga panel showing character's journey in {manga_style}",
            "music_prompt": f"Emotional music for panel {panel_number}",
            "tts_text": dialogue_content,
            "user_mood": inputs.mood if inputs else "neutral",
            "user_vibe": getattr(inputs, "vibe", "calm") if inputs else "calm",
        }

    def _generate_meaningful_dialogue(
        self, panel_number: int, inputs: StoryInputs
    ) -> str:
        """Generate meaningful dialogue content for fallback panels."""
        name = inputs.nickname if inputs else "our hero"
        dream = inputs.dream if inputs else "their goals"
        mood = inputs.mood if inputs else "uncertain"

        dialogue_map = {
            1: f"Meet {name}. They're feeling {mood} today, but deep inside burns a desire to {dream}. Every great journey begins with a single step forward.",
            2: f"{name} faces the challenge ahead. The path to {dream} isn't easy, but they've come too far to give up now. Sometimes the hardest battles are the ones we fight within ourselves.",
            3: f"Taking a moment to breathe, {name} reflects on how far they've already come. Even when feeling {mood}, there's strength in acknowledging both struggles and progress.",
            4: f"In this moment of clarity, {name} discovers something important. Their {dream} isn't just about the destination - it's about becoming the person they're meant to be along the way.",
            5: f"With newfound determination, {name} takes action. They realize that being {mood} doesn't define them - it's just one part of their story, and they have the power to write the next chapter.",
            6: f"Looking back on the journey, {name} sees how much they've grown. The road to {dream} continues, but now they know they have the strength to face whatever comes next. Hope lights the way forward.",
        }

        return dialogue_map.get(
            panel_number,
            f"{name} continues their journey toward {dream}, growing stronger with each step.",
        )
