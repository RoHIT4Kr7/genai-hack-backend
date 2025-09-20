"""
Enhanced dialogue extraction service to handle complex LLM responses.
"""

import re
import json
from typing import Dict, List, Any, Optional
from loguru import logger


class DialogueExtractor:
    """
    Advanced dialogue extraction that handles various LLM response formats.
    """

    @staticmethod
    def extract_all_panels_robust(text: str) -> Dict[int, str]:
        """
        Extract dialogue from all panels using multiple parsing strategies.

        Args:
            text: Raw LLM response text

        Returns:
            Dictionary mapping panel number to dialogue text
        """
        # Normalize line endings and strip code fences/surrounding markdown for more reliable regex
        cleaned = text.replace("\r\n", "\n").replace("\r", "\n")
        cleaned = re.sub(r"```[a-zA-Z]*\n?|```", "", cleaned)

        panels = {}

        # Strategy 1: Standard format with quotes
        strategy1_pattern = r'PANEL_(\d+):\s*dialogue_text:\s*"([^"]*)"'
        matches = re.findall(strategy1_pattern, cleaned, re.DOTALL)
        for panel_num, dialogue in matches:
            if dialogue.strip() and len(dialogue.strip()) > 10:
                panels[int(panel_num)] = dialogue.strip()

        # Strategy 2: Format without quotes
        if len(panels) < 6:
            strategy2_pattern = r"PANEL_(\d+):\s*dialogue_text:\s*([^\n]+)"
            matches = re.findall(strategy2_pattern, cleaned, re.DOTALL)
            for panel_num, dialogue in matches:
                panel_int = int(panel_num)
                if (
                    panel_int not in panels
                    and dialogue.strip()
                    and len(dialogue.strip()) > 10
                ):
                    panels[panel_int] = dialogue.strip()

        # Strategy 3: More flexible pattern
        if len(panels) < 6:
            strategy3_pattern = (
                r'PANEL\s*(\d+)[:\s]*.*?dialogue[_\s]*text[:\s]*["\']?([^"\'\n]+)["\']?'
            )
            matches = re.findall(strategy3_pattern, cleaned, re.DOTALL | re.IGNORECASE)
            for panel_num, dialogue in matches:
                panel_int = int(panel_num)
                if (
                    panel_int not in panels
                    and dialogue.strip()
                    and len(dialogue.strip()) > 10
                ):
                    panels[panel_int] = dialogue.strip()

        # Strategy 3b: Section-based multi-line extraction
        if len(panels) < 6:
            for i in range(1, 7):
                if i in panels:
                    continue
                # Find the start of the panel section allowing PANEL_1 or PANEL 1 or Panel 1
                start_match = re.search(
                    rf"(?:PANEL[_\s]|Panel\s){i}\s*:\s*", cleaned, re.IGNORECASE
                )
                if not start_match:
                    continue
                start_idx = start_match.end()
                # Find the end of this panel section (next PANEL or end of text)
                end_match = re.search(
                    rf"(?:PANEL[_\s]|Panel\s){i+1}\s*:\s*|CHARACTER_SHEET\s*:|PROP_SHEET\s*:|STYLE_GUIDE\s*:",
                    cleaned[start_idx:],
                    re.IGNORECASE,
                )
                end_idx = start_idx + (
                    end_match.start() if end_match else len(cleaned) - start_idx
                )
                section = cleaned[start_idx:end_idx]

                # Within section, look for dialogue_text value that may span multiple lines until a blank line or another key
                # Pattern 1: dialogue_text: "..." (possibly multi-line within quotes)
                m = re.search(
                    r'dialogue[_\s]*text\s*:\s*"([\s\S]*?)"\s*(?:\n\s*\w+\s*:|$)',
                    section,
                    re.IGNORECASE,
                )
                if not m:
                    # Pattern 2: dialogue_text: (value on next lines) until double newline or next key
                    m = re.search(
                        r"dialogue[_\s]*text\s*:\s*([\s\S]*?)(?:\n\s*\n|\n\s*\w+\s*:|$)",
                        section,
                        re.IGNORECASE,
                    )
                if m:
                    dialogue_text = m.group(1).strip()
                    # Clean enclosing quotes or bullet markers
                    dialogue_text = re.sub(r'^["\']|["\']$', "", dialogue_text)
                    # Collapse whitespace and newlines to spaces
                    dialogue_text = re.sub(r"\s*\n\s*", " ", dialogue_text)
                    if len(dialogue_text) > 10:
                        panels[i] = dialogue_text

        # Strategy 4: Look for numbered dialogue blocks
        if len(panels) < 6:
            strategy4_pattern = r"(\d+)[\.:\s]+([^0-9\n][^\n]{20,})"
            matches = re.findall(strategy4_pattern, cleaned, re.DOTALL)
            panel_counter = 1
            for num_str, dialogue in matches:
                if panel_counter <= 6 and panel_counter not in panels:
                    clean_dialogue = dialogue.strip().rstrip(".")
                    if len(clean_dialogue) > 15:
                        panels[panel_counter] = clean_dialogue
                        panel_counter += 1

        logger.info(
            f"Extracted dialogue for {len(panels)} panels using robust extraction"
        )
        return panels

    @staticmethod
    def validate_and_enhance_dialogue(
        panels: Dict[int, str], inputs: Any
    ) -> Dict[int, str]:
        """
        Validate extracted dialogue and enhance with meaningful content if needed.

        Args:
            panels: Extracted panel dialogue
            inputs: Story inputs for fallback generation

        Returns:
            Enhanced panel dialogue dictionary
        """
        enhanced_panels = {}
        name = getattr(inputs, "nickname", "our hero") if inputs else "our hero"
        dream = getattr(inputs, "dream", "their goals") if inputs else "their goals"
        mood = getattr(inputs, "mood", "uncertain") if inputs else "uncertain"

        # Meaningful fallback content
        fallback_dialogues = {
            1: f"Meet {name}. They're feeling {mood} today, but deep inside burns a desire to achieve {dream}. Every great journey begins with a single step forward.",
            2: f"{name} faces the challenge ahead. The path to {dream} isn't easy, but they've come too far to give up now. Sometimes the hardest battles are the ones we fight within ourselves.",
            3: f"Taking a moment to breathe, {name} reflects on how far they've already come. Even when feeling {mood}, there's strength in acknowledging both struggles and progress.",
            4: f"In this moment of clarity, {name} discovers something important. Their {dream} isn't just about the destination - it's about becoming the person they're meant to be along the way.",
            5: f"With newfound determination, {name} takes action. They realize that being {mood} doesn't define them - it's just one part of their story, and they have the power to write the next chapter.",
            6: f"Looking back on the journey, {name} sees how much they've grown. The road to {dream} continues, but now they know they have the strength to face whatever comes next. Hope lights the way forward.",
        }

        for panel_num in range(1, 7):
            if panel_num in panels and len(panels[panel_num]) > 20:
                # Use extracted dialogue if it's substantial
                enhanced_panels[panel_num] = panels[panel_num]
            else:
                # Use meaningful fallback
                enhanced_panels[panel_num] = fallback_dialogues[panel_num]
                logger.info(f"Using enhanced fallback dialogue for panel {panel_num}")

        return enhanced_panels


# Global instance
dialogue_extractor = DialogueExtractor()
