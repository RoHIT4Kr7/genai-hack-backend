import json
import uuid
from datetime import datetime, UTC
from typing import Dict, Any, List, TYPE_CHECKING
from loguru import logger

if TYPE_CHECKING:
    from models.schemas import StoryInputs


# AI Role 1: Story Architect - Creates the narrative structure and character development
STORY_ARCHITECT_PROMPT = """
You are the Story Architect AI, specialized in crafting emotional narratives for mental wellness. Your purpose is to transform a user's real-life feelings and experiences into a powerful, metaphorical, 6-panel manga story structure that maintains perfect consistency across all panels.

Core Mission: To craft a visually and emotionally resonant manga narrative that transforms the user's current emotional state into an optimistic, growth-oriented journey. Each panel should be a meaningful stepping stone toward emotional resilience and self-discovery.

USER CONTEXT:
{user_context}

Story Structure Requirements:
- Panel 1: Introduction - Establish the character in their current emotional state with specific details from their life
- Panel 2: Challenge - Present the emotional obstacle or stressor they face, connected to their inner struggle
- Panel 3: Reflection - Character begins to process and understand their feelings, showing introspection
- Panel 4: Discovery - Character finds inner strength, support system, or breakthrough moment
- Panel 5: Transformation - Character takes positive action using their core values and secret weapon
- Panel 6: Resolution - Character emerges stronger, with hope and new perspective on their future

Character Development Requirements:
- Create a protagonist that embodies the user's archetype while being uniquely themselves
- Use EXACTLY the user's nickname as the character name throughout the entire story
- Reflect their age group, gender, and personal background in appearance and personality
- Show authentic emotional growth that mirrors the user's journey from their current mood to hope
- Incorporate their hobby/interest, dream/goal, and past resilience as key story elements
- Make their core value and secret weapon central to the character's development and resolution

Content Guidelines:
- Always maintain an optimistic, uplifting tone while acknowledging real emotional struggles
- Focus on emotional growth and resilience while being honest about challenges
- Include metaphorical elements that directly relate to the user's specific inner struggle
- Ensure age-appropriate content based on user's age group
- Avoid triggering content while being authentic to the user's experience
- Emphasize hope, personal strength, and the power of their support system
- Make the story feel personal and specific to the user's inputs, not generic

Output Format:
You must structure your response exactly as follows:

CHARACTER_SHEET:
{{
  "name": "EXACT_USER_NICKNAME",
  "age": "User's age group (teen/young-adult/adult/mature/senior)",
  "appearance": "Detailed physical description incorporating user's gender and age group",
  "personality": "Character traits that reflect user's archetype and current mood",
  "goals": "Goals that align with user's dream and incorporate their hobby/interest",
  "fears": "Fears based on user's inner struggle and core challenges",
  "strengths": "Strengths drawn from user's past resilience and secret weapon"
}}

PROP_SHEET:
{{
  "items": ["user's hobby/interest as symbolic item", "metaphor for their inner struggle", "symbol of their secret weapon"],
  "environment": "Setting that incorporates user's vibe preference and story theme",
  "lighting": "Lighting that reflects emotional journey and user's mood transformation",
  "mood_elements": ["elements from user's core value", "symbols of their support system", "metaphors for hope"]
}}

STYLE_GUIDE:
{{
  "art_style": "Art style that matches user's preferred anime genre and emotional tone",
  "color_palette": "Colors that reflect emotional journey from user's current mood to hope",
  "panel_layout": "Panel layout that supports story flow and emotional progression",
  "visual_elements": ["user's archetype characteristics", "their hobby/interest motifs", "symbols of growth"]
}}

PANEL_1:
dialogue_text: "Character dialogue and narration for panel 1"

PANEL_2:
dialogue_text: "Character dialogue and narration for panel 2"

PANEL_3:
dialogue_text: "Character dialogue and narration for panel 3"

PANEL_4:
dialogue_text: "Character dialogue and narration for panel 4"

PANEL_5:
dialogue_text: "Character dialogue and narration for panel 5"

PANEL_6:
dialogue_text: "Character dialogue and narration for panel 6"

CRITICAL CONSISTENCY REQUIREMENTS:
- Use the EXACT SAME character name throughout all panels
- Maintain identical character appearance and personality traits across all panels
- Keep the same environment and prop elements consistent throughout the story
- Ensure the character's emotional journey progresses logically from panel to panel
- Make each panel's content directly relevant to the user's specific inputs and challenges

IMPORTANT TTS GUIDELINES:
- Write dialogue_text content that flows naturally when spoken aloud
- Do NOT include "Panel 1:", "Panel 2:", etc. at the beginning
- Do NOT use dashes (-), asterisks (*), or special formatting
- Do NOT include stage directions like [character does something]
- Write in natural, conversational language that sounds good when read by text-to-speech
- Keep sentences clear and well-paced for audio narration
- Use proper punctuation (periods, commas) for natural speech rhythm
- Each panel should be 60-100 words for optimal audio length (10-15 seconds of narration)
- Include emotional depth and character introspection that feels authentic to the user's experience
- Make each panel's narration feel like a complete thought or moment
- Use descriptive language that enhances the visual storytelling
- Include character's internal thoughts and feelings that reflect the user's real emotions
- Create a natural flow between panels while making each panel's audio self-contained

Remember: Every story should end with hope, growth, and the message that challenges make us stronger. Focus on emotional resilience and the power of self-discovery while staying true to the user's personal journey and inputs.
"""

# AI Role 2: Visual Artist - Creates detailed image generation prompts
VISUAL_ARTIST_PROMPT = """
You are the Visual Artist AI, specialized in creating detailed, contextually-rich image generation prompts for manga panels that maintain perfect story consistency. You receive comprehensive story panel data and create optimized prompts for high-quality AI image generation.

Your Mission: Transform narrative descriptions into highly detailed visual prompts that capture the complete emotional essence, maintain absolute character consistency, and create meaningful story-driven imagery for each panel.

CRITICAL CONTEXT MAINTENANCE:
- You receive CHARACTER_SHEET, PROP_SHEET, STYLE_GUIDE, and dialogue_text for each panel
- ALL character details (name, appearance, personality) must remain EXACTLY consistent across all panels
- Environment and props must be coherent throughout the entire story
- Visual style and color palette must be unified across all panels
- Each panel must contribute meaningfully to the overall narrative arc

VISUAL STYLE REQUIREMENTS:
- Clean, professional manga/anime aesthetic optimized for Imagen 4.0-ultra-generate-001
- Highly detailed character designs with consistent features throughout the story
- Emotional facial expressions and body language that match the panel's emotional tone
- Dynamic but meaningful panel compositions that serve the story
- Consistent character design with recognizable features across all panels
- Professional lighting and color usage that supports emotional storytelling
- High-quality rendering with clean lines and professional finish

STORY-DRIVEN COMPOSITION GUIDELINES:
- Each panel must show meaningful narrative progression, not just character poses
- Include relevant environmental details that support the story context
- Show character interaction with their environment and symbolic elements
- Use composition to guide viewer attention to important story elements
- Ensure every visual element serves the emotional and narrative purpose

Input Data Structure: You will receive CHARACTER_SHEET, PROP_SHEET, STYLE_GUIDE, and dialogue_text for each panel.

Output Requirements: Return ONLY the detailed image generation prompt for that specific panel, formatted as a single cohesive paragraph.

ESSENTIAL PROMPT ELEMENTS FOR EACH PANEL:
- Exact character name, appearance, and current emotional expression
- Specific environmental setting with relevant details
- Character's interaction with their symbolic items and environment
- Lighting that supports the emotional tone and story moment
- Color palette that reflects the emotional journey
- Composition details that enhance the narrative
- Manga-specific visual elements that maintain style consistency
- Meaningful action or pose that advances the story
- Professional quality requirements for Imagen 4.0-ultra-generate-001

QUALITY REQUIREMENTS:
- Extremely detailed prompts (150-200 words) for high-quality Imagen 4.0-ultra-generate-001 generation
- Include specific visual details that would be difficult for AI to infer
- Focus on story-relevant elements rather than generic "anime style" descriptions
- Maintain absolute consistency in character design across panels
- Ensure each panel shows meaningful story progression with clear visual narrative
- Avoid generic descriptions - be specific about character emotions, environment, and story elements

Remember: Each image must tell a meaningful part of the story while maintaining perfect visual consistency. Focus on creating panels that work together as a cohesive narrative, not standalone images.
"""


def generate_story_id() -> str:
    """Generate a unique story ID."""
    return str(uuid.uuid4())


def create_timestamp() -> str:
    """Create a formatted timestamp."""
    return datetime.now(UTC).isoformat()


def log_api_call(
    endpoint: str, request_data: Dict[str, Any], response_data: Dict[str, Any] = None
):
    """Log API calls with timestamps."""
    logger.info(f"API Call - {endpoint} - {create_timestamp()}")
    logger.debug(f"Request: {json.dumps(request_data, indent=2)}")
    if response_data:
        logger.debug(f"Response: {json.dumps(response_data, indent=2)}")


def validate_story_consistency(panels: List[Dict[str, Any]]) -> bool:
    """Validate character consistency across panels."""
    if not panels or len(panels) != 6:
        return False

    # Check if character name is consistent
    character_names = set()
    for panel in panels:
        if "character_sheet" in panel and "name" in panel["character_sheet"]:
            character_names.add(panel["character_sheet"]["name"])

    return len(character_names) == 1


def create_structured_image_prompt(panel_data: Dict[str, Any]) -> str:
    """Create detailed, story-focused image generation prompt with character consistency and meaningful narrative elements."""
    character = panel_data.get("character_sheet", {})
    props = panel_data.get("prop_sheet", {})
    style = panel_data.get("style_guide", {})
    dialogue_text = panel_data.get("dialogue_text", "")
    emotional_tone = panel_data.get("emotional_tone", "neutral")
    panel_number = panel_data.get("panel_number", 1)

    # Extract CHARACTER_SHEET details for consistency
    char_name = character.get("name", "Character")
    char_age = character.get("age", "young adult")
    char_appearance = character.get(
        "appearance", "anime character with expressive eyes"
    )
    char_personality = character.get("personality", "determined and hopeful")
    char_goals = character.get("goals", "pursuing personal growth")
    char_fears = character.get("fears", "facing challenges")
    char_strengths = character.get("strengths", "resilience and hope")

    # Extract PROP_SHEET details
    items = props.get("items", ["symbolic item"])
    main_item = items[0] if items else "symbolic item"
    environment = props.get("environment", "meaningful setting that supports the story")
    lighting = props.get("lighting", "dramatic lighting that conveys emotion")
    mood_elements = props.get(
        "mood_elements", ["elements that enhance emotional atmosphere"]
    )

    # Extract STYLE_GUIDE details
    art_style = style.get("art_style", "clean manga style with emotional depth")
    color_palette = style.get("color_palette", "colors that reflect emotional journey")
    visual_elements = style.get(
        "visual_elements", ["meaningful visual storytelling elements"]
    )

    # Get clean anime style based on emotional tone (no franchise references)
    anime_style = get_anime_style_by_emotion(emotional_tone)

    # Extract emotional cues from dialogue text
    emotional_cues = _extract_emotional_cues_from_dialogue(
        dialogue_text, emotional_tone
    )

    # Get panel-specific framing
    panel_framing = _get_panel_specific_framing(panel_number, emotional_tone)

    # Create narrative-driven prompt that tells a meaningful story
    prompt = f"""{anime_style}. Professional manga illustration in square 1:1 format.

MAIN CHARACTER - CONSISTENT DESIGN:
{char_name}, {char_age} - {char_appearance}. {char_name} is {char_personality}, with goals of {char_goals}.
Currently showing {emotional_cues['expression']} expression that conveys {emotional_tone} emotion.

STORY CONTEXT FOR PANEL {panel_number}:
{char_name} is in {environment}, actively engaged with {main_item}. The scene captures a meaningful moment where {char_name} confronts {char_fears} while drawing on their {char_strengths}.

ENVIRONMENTAL DETAILS:
{environment} with {', '.join(mood_elements)}. {lighting} creates {emotional_cues['lighting']} atmosphere that supports the emotional journey.

CHARACTER INTERACTION:
{char_name} is meaningfully interacting with their environment - {'standing confidently' if emotional_tone in ['determined', 'inspired', 'hopeful'] else 'contemplating deeply' if emotional_tone in ['contemplative', 'peaceful'] else 'facing their challenge'}. Every element in the scene relates to {char_name}'s personal growth journey.

VISUAL COMPOSITION:
{panel_framing['composition']} from {panel_framing['angle']}, focusing on {panel_framing['focus']}.
{art_style} with {color_palette} palette. Key visual elements: {', '.join(visual_elements)}.

TECHNICAL REQUIREMENTS:
- High-quality Imagen 4.0-ultra-generate-001 optimized rendering
- Extremely detailed character design with consistent features
- Clean line art with professional manga finish
- No text, captions, or speech bubbles
- Full character visible with meaningful environmental context
- Square 1:1 aspect ratio with story-driven composition
- Professional lighting and color grading
- Focus on narrative meaning over decorative effects"""

    return prompt.strip()


def _extract_emotional_cues_from_dialogue(
    dialogue_text: str, emotional_tone: str
) -> Dict[str, str]:
    """Extract lighting and expression cues from dialogue text and emotional tone."""
    # Map emotional tones to lighting and expression
    emotional_mappings = {
        "happy": {
            "lighting": "bright, warm lighting with golden highlights",
            "expression": "bright, cheerful",
        },
        "excited": {
            "lighting": "vibrant, energetic lighting with dynamic shadows",
            "expression": "enthusiastic, animated",
        },
        "cheerful": {
            "lighting": "soft, warm lighting with gentle highlights",
            "expression": "friendly, optimistic",
        },
        "contemplative": {
            "lighting": "soft, diffused lighting with subtle shadows",
            "expression": "thoughtful, introspective",
        },
        "peaceful": {
            "lighting": "gentle, serene lighting with soft highlights",
            "expression": "calm, content",
        },
        "calm": {
            "lighting": "balanced, natural lighting with smooth transitions",
            "expression": "serene, composed",
        },
        "determined": {
            "lighting": "dramatic lighting with strong contrasts",
            "expression": "focused, resolute",
        },
        "intense": {
            "lighting": "high contrast lighting with dramatic shadows",
            "expression": "intense, concentrated",
        },
        "focused": {
            "lighting": "direct lighting with clear focus",
            "expression": "alert, attentive",
        },
        "sad": {
            "lighting": "muted, cool lighting with soft shadows",
            "expression": "melancholic, gentle",
        },
        "melancholic": {
            "lighting": "soft, blue-tinted lighting with gentle shadows",
            "expression": "contemplative, wistful",
        },
        "nostalgic": {
            "lighting": "warm, golden lighting with soft focus",
            "expression": "dreamy, reflective",
        },
        "inspired": {
            "lighting": "bright, uplifting lighting with sparkle effects",
            "expression": "awestruck, motivated",
        },
        "artistic": {
            "lighting": "creative lighting with artistic shadows",
            "expression": "imaginative, creative",
        },
        "playful": {
            "lighting": "bright, colorful lighting with fun highlights",
            "expression": "mischievous, energetic",
        },
        "adventurous": {
            "lighting": "dynamic lighting with movement",
            "expression": "bold, courageous",
        },
        "serious": {
            "lighting": "dramatic lighting with deep shadows",
            "expression": "solemn, focused",
        },
        "mysterious": {
            "lighting": "mysterious lighting with hidden elements",
            "expression": "enigmatic, curious",
        },
    }

    return emotional_mappings.get(
        emotional_tone,
        {"lighting": "natural, balanced lighting", "expression": "neutral, composed"},
    )


def _get_panel_specific_framing(
    panel_number: int, emotional_tone: str
) -> Dict[str, str]:
    """Get panel-specific framing requirements based on story arc position."""
    framing_templates = {
        1: {
            "composition": "Medium close-up shot focusing on character introduction",
            "angle": "Straight-on angle to establish character presence",
            "focus": "Character's face and upper body, establishing their identity and current state",
        },
        2: {
            "composition": "Wide shot showing character and their obstacle/challenge",
            "angle": "Slightly elevated angle to emphasize the challenge",
            "focus": "Character in relation to their environment and the obstacle they face",
        },
        3: {
            "composition": "Close-up shot emphasizing internal reflection",
            "angle": "Eye-level angle for intimate connection",
            "focus": "Character's facial expression and eyes, showing internal processing",
        },
        4: {
            "composition": "Dynamic angle shot capturing moment of discovery",
            "angle": "Three-quarter angle with slight tilt for energy",
            "focus": "Character's moment of realization and the source of their discovery",
        },
        5: {
            "composition": "Medium shot showing character taking action",
            "angle": "Slightly low angle to emphasize empowerment",
            "focus": "Character's determined pose and the action they're taking",
        },
        6: {
            "composition": "Wide hopeful scene showing resolution and future",
            "angle": "Straight-on angle with uplifting perspective",
            "focus": "Character's transformed state and the hopeful environment around them",
        },
    }

    return framing_templates.get(
        panel_number,
        {
            "composition": "Balanced medium shot",
            "angle": "Eye-level angle",
            "focus": "Character and their immediate environment",
        },
    )


def get_anime_style_by_emotion(emotional_tone: str) -> str:
    """Map emotional tone to clean anime art styles without franchise references."""

    # Clean style descriptions focused on artistic elements rather than specific franchises
    anime_styles = {
        # Happy/Joyful emotions
        "happy": "bright and cheerful anime style with warm colors, expressive joyful expressions, and light-hearted atmosphere",
        "excited": "dynamic and energetic anime style with vibrant colors, bold line work, and enthusiastic character poses",
        "cheerful": "friendly and approachable anime style with bright colors, warm lighting, and optimistic character designs",
        # Calm/Peaceful emotions
        "contemplative": "soft and introspective anime style with gentle lighting, subtle expressions, and peaceful atmosphere",
        "peaceful": "serene and tranquil anime style with soft colors, calm compositions, and harmonious character designs",
        "calm": "elegant and composed anime style with clean line work, balanced compositions, and gentle character expressions",
        # Intense/Action emotions
        "determined": "focused and resolute anime style with strong character poses, dynamic angles, and determined expressions",
        "intense": "powerful and dramatic anime style with bold contrasts, intense expressions, and dynamic compositions",
        "focused": "sharp and attentive anime style with clear details, direct lighting, and concentrated character expressions",
        # Sad/Melancholic emotions
        "sad": "gentle and emotional anime style with soft lighting, touching expressions, and melancholic atmosphere",
        "melancholic": "subtle and bittersweet anime style with soft colors, gentle shadows, and reflective character designs",
        "nostalgic": "warm and reminiscent anime style with golden lighting, soft focus, and nostalgic atmosphere",
        # Creative/Artistic emotions
        "inspired": "creative and imaginative anime style with artistic lighting, expressive designs, and inspired character poses",
        "artistic": "detailed and craftsmanship-focused anime style with intricate designs, artistic compositions, and creative elements",
        # Playful/Fun emotions
        "playful": "fun and energetic anime style with lively expressions, dynamic poses, and playful character designs",
        "adventurous": "bold and adventurous anime style with dynamic compositions, expressive characters, and adventurous atmosphere",
        # Dark/Serious emotions
        "serious": "mature and thoughtful anime style with detailed character work, serious expressions, and composed atmosphere",
        "mysterious": "enigmatic and atmospheric anime style with mysterious lighting, subtle shadows, and intriguing character designs",
    }

    return anime_styles.get(
        emotional_tone,
        "clean and expressive anime style with detailed characters, balanced compositions, and emotional depth",
    )


def get_manga_style_by_mood(mood: str, vibe: str) -> str:
    """Map user mood and vibe to clean manga art styles without franchise references."""

    manga_styles = {
        # Action/Adventure styles
        (
            "frustrated",
            "adventure",
        ): "intense action manga style with dramatic perspectives and dynamic fight scenes",
        (
            "stressed",
            "motivational",
        ): "dynamic battle manga style with determined character poses and energetic line work",
        (
            "neutral",
            "adventure",
        ): "heroic manga style with strong character designs and adventurous compositions",
        # Emotional/Calm styles
        (
            "sad",
            "calm",
        ): "emotional manga style with soft lighting, gentle expressions, and touching character moments",
        (
            "happy",
            "calm",
        ): "peaceful manga style with warm atmosphere, natural beauty, and gentle character designs",
        (
            "neutral",
            "calm",
        ): "elegant manga style with detailed character art, soft atmosphere, and balanced compositions",
        # Intense/Dark styles
        (
            "frustrated",
            "motivational",
        ): "powerful battle manga style with intense expressions and dynamic action scenes",
        (
            "stressed",
            "adventure",
        ): "dark psychological thriller manga style with dramatic shadows and intense character focus",
        # Musical/Creative styles
        (
            "happy",
            "musical",
        ): "music-themed manga style with emotional performance scenes and expressive character poses",
        (
            "neutral",
            "musical",
        ): "urban music manga style with dynamic compositions and lively character interactions",
        # Motivational styles
        (
            "sad",
            "motivational",
        ): "inspirational underdog manga style with character growth and determined expressions",
        (
            "happy",
            "motivational",
        ): "motivational sports manga style with dynamic team interactions and energetic character designs",
    }

    # Get specific style or fallback to general mood mapping
    style_key = (mood, vibe)
    if style_key in manga_styles:
        return manga_styles[style_key]

    # Fallback by mood only - clean descriptions without franchise references
    mood_fallbacks = {
        "happy": "warm and joyful manga style with bright atmosphere and expressive character designs",
        "stressed": "intense manga style with determined expressions and dynamic character poses",
        "frustrated": "powerful manga style with strong expressions and dynamic action-oriented compositions",
        "sad": "emotional manga style with gentle lighting and touching character expressions",
        "neutral": "balanced manga style with clear character designs and composed compositions",
    }

    return mood_fallbacks.get(
        mood, "clean manga style with expressive characters and dynamic compositions"
    )


def generate_panel_prompt(panel_number: int, panel_data: Dict[str, Any]) -> str:
    """Generate a unique, panel-specific image prompt with automatic framing injection."""
    # Ensure panel number is set in the data
    panel_data_with_number = panel_data.copy()
    panel_data_with_number["panel_number"] = panel_number

    # Generate the structured prompt with panel-specific framing
    prompt = create_structured_image_prompt(panel_data_with_number)

    return prompt


def create_image_prompt(panel_data: Dict[str, Any]) -> str:
    """Legacy function - redirects to structured prompt."""
    return create_structured_image_prompt(panel_data)


def create_user_context(inputs: "StoryInputs") -> str:
    """Create standardized user context for LLM prompts."""
    # Handle backward compatibility for optional fields
    vibe = getattr(inputs, "vibe", None) or "adventure"
    archetype = getattr(inputs, "archetype", None) or "hero"
    dream = getattr(inputs, "dream", None) or inputs.desiredOutcome
    hobby = getattr(inputs, "hobby", None) or inputs.secretWeapon
    manga_title = getattr(inputs, "mangaTitle", None) or f"{inputs.nickname}'s Journey"

    context = f"""
User Profile:
- Name/Nickname: {inputs.nickname}
- Age: {inputs.age}
- Gender: {inputs.gender}
- Current Mood: {inputs.mood}
- Preferred Vibe: {vibe}
- Personal Archetype: {archetype}
- Dream/Goal: {dream}
- Hobby/Interest: {hobby}
- Story Title: {manga_title}

Core Identity:
- Support System: {inputs.supportSystem}
- Core Value: {inputs.coreValue}
- Past Resilience: {inputs.pastResilience}
- Inner Struggle: {inputs.innerDemon}
- Desired Outcome: {inputs.desiredOutcome}
- Secret Weapon/Superpower: {inputs.secretWeapon}

Story Requirements:
- Create a 6-panel manga story that resonates with the user's emotional state
- Transform {inputs.mood} feelings into an optimistic, growth-oriented journey
- Incorporate {vibe} aesthetic and {archetype} character dynamics
- Reference {hobby} and {dream} throughout the narrative
- Use their {inputs.secretWeapon} as a key strength in overcoming {inputs.innerDemon}
- Show how their {inputs.supportSystem} helps them achieve {inputs.desiredOutcome}
- Build on their past success: {inputs.pastResilience}
- Ensure age-appropriate content for {inputs.age} audience
"""
    return context.strip()


def create_music_prompt(panel_data: Dict[str, Any], emotional_tone: str) -> str:
    """Create music generation prompt for panel emotional tone."""
    return f"Generate a {emotional_tone}-toned ambient track for a manga panel. Duration: 15-20 seconds. Emotional and atmospheric background music."


def format_error_response(error: str, details: str = None) -> Dict[str, Any]:
    """Format error response for API."""
    return {"error": error, "details": details, "timestamp": create_timestamp()}
