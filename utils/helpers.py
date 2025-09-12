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
  "art_style": "Professional anime illustration style with vibrant cel-shading, expressive character animation, and detailed background art. Think high-quality anime production with emotional depth - combining the atmospheric beauty of Studio Ghibli with the dynamic energy of modern anime. The character design must be completely original and unique.",
  "color_palette": "Dynamic anime color grading that evolves with the emotional journey: Panels 1-2 use muted, contemplative tones (soft blues, grays, pastels), Panels 3-4 transition to warmer colors (gentle oranges, soft yellows), Panels 5-6 burst with vibrant, hopeful colors (bright blues, energetic oranges, triumphant golds) with anime-style lighting effects.",
  "panel_layout": "Cinematic anime scenes in square 1:1 format - each panel is a complete anime illustration with professional composition, not traditional manga panels. Use anime directing techniques like dynamic camera angles, dramatic lighting, and atmospheric effects.",
  "visual_elements": ["anime-style particle effects (sparkles, light orbs, energy aura)", "environmental anime effects (wind through hair, floating petals, gentle mist)", "anime lighting techniques (rim lighting, god rays, soft shadows)", "symbolic elements from user's life rendered in anime aesthetic", "anime-specific atmospheric details (lens flares, bokeh effects, soft focus backgrounds)"]
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

IMPORTANT TTS GUIDELINES FOR 8-10 SECOND VOICE CONTENT:
- Write dialogue_text content that flows naturally when spoken aloud as pure narration
- Do NOT include "Panel 1:", "Panel 2:", etc. at the beginning
- Do NOT use quotes ("), dashes (-), asterisks (*), or special formatting symbols
- Do NOT include stage directions like [character does something] or (character action)
- Do NOT use ellipses (...) or em dashes (—) - replace with natural pauses using commas
- Write in natural, conversational language that sounds perfect for text-to-speech
- Keep sentences clear and well-paced for smooth audio narration
- Use proper punctuation (periods, commas) for natural speech rhythm
- Each panel should be 25-35 words for optimal 8-10 second audio duration
- Focus on character's internal voice and emotional journey without narrative descriptions
- Make each panel's voice content feel like the character speaking directly to the listener
- Use simple, clear language that conveys deep emotional meaning
- Include character's genuine thoughts and feelings that reflect the user's real experience
- Create smooth emotional progression between panels while making each self-contained
- End sentences naturally without trailing punctuation or incomplete thoughts

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
    """Create a detailed, anime-focused image prompt with original character design protection."""
    character = panel_data.get("character_sheet", {})
    props = panel_data.get("prop_sheet", {})
    style = panel_data.get("style_guide", {})
    dialogue_text = panel_data.get("dialogue_text", "")
    emotional_tone = panel_data.get("emotional_tone", "neutral")
    panel_number = panel_data.get("panel_number", 1)

    # Extract CHARACTER_SHEET details for consistency
    char_name = character.get("name", "Character")
    char_appearance = character.get(
        "appearance", "anime character with expressive eyes"
    )
    char_age = character.get("age", "young adult")
    char_personality = character.get("personality", "determined and hopeful")

    # Extract PROP_SHEET details
    items = props.get("items", ["symbolic item"])
    environment = props.get("environment", "meaningful setting that supports the story")
    lighting = props.get("lighting", "dramatic lighting that conveys emotion")
    mood_elements = props.get(
        "mood_elements", ["elements that enhance emotional atmosphere"]
    )

    # Get anime style with detailed visual effects
    user_mood = panel_data.get("user_mood", "neutral")
    user_vibe = panel_data.get("user_vibe", "calm")
    anime_aesthetic = get_anime_style_by_mood(user_mood, user_vibe)

    # Get panel-specific framing
    panel_framing = _get_panel_specific_framing(panel_number, emotional_tone)

    # Create anime-specific environmental effects
    anime_effects = _get_anime_environmental_effects(emotional_tone, user_mood)

    # ENHANCED ANIME-FOCUSED PROMPT TEMPLATE
    prompt = f"""ANIME SCENE: High-quality anime illustration with professional cel-shading and vibrant colors.

**VISUAL STYLE & ATMOSPHERE:**
{anime_aesthetic}

**ORIGINAL CHARACTER (NO EXISTING ANIME RESEMBLANCE):**
- **Identity:** An original anime character named {char_name}, {char_age}, with {char_personality} personality
- **Unique Design:** {char_appearance} - MUST be completely original design, not resembling any existing anime characters
- **Expression:** Showing {emotional_tone} emotion through authentic anime facial expressions and body language
- **Narrative Context:** {dialogue_text}

**ANIME SCENE COMPOSITION:**
- **Camera Work:** {panel_framing['composition']} with {panel_framing['angle']} - cinematic anime directing style
- **Focus Point:** {panel_framing['focus']} with dramatic anime emphasis techniques
- **Environment:** {environment} rendered in detailed anime background art style
- **Symbolic Elements:** {', '.join(mood_elements)} integrated naturally into the anime scene

**ANIME VISUAL EFFECTS:**
{anime_effects}

**LIGHTING & COLOR:**
- **Lighting Style:** {lighting} with anime-specific rim lighting and soft shadows
- **Color Grading:** Vibrant anime color palette with proper saturation and contrast
- **Atmospheric Effects:** Soft particles, gentle wind effects, and anime-style environmental details

**TECHNICAL SPECIFICATIONS:**
- **Art Style:** Professional anime illustration with clean line art and cel-shading
- **Quality:** High-definition anime artwork suitable for animation production
- **Format:** Square 1:1 aspect ratio anime panel
- **Character Consistency:** Maintain exact same character design as established in reference

**CRITICAL RESTRICTIONS:**
- NO text, speech bubbles, logos, or watermarks
- Character MUST be 100% original - absolutely NO resemblance to Naruto, Luffy, Goku, Ichigo, or ANY existing anime characters
- Focus on ANIME AESTHETIC and VISUAL STYLE without copying character designs
- Use anime themes and atmosphere while keeping character completely unique

Panel {panel_number} of 6: This anime scene represents a key moment in {char_name}'s emotional journey toward hope and resilience.""".strip()

    return prompt


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


def _get_anime_environmental_effects(emotional_tone: str, mood: str) -> str:
    """Generate anime-specific environmental effects based on emotion and mood."""

    effect_combinations = {
        # Happy emotions
        (
            "happy",
            "cheerful",
        ): "Floating cherry blossom petals, warm sunbeams with lens flares, gentle sparkle particles, and soft wind effects moving through hair and clothing",
        (
            "happy",
            "excited",
        ): "Dynamic speed lines, energy sparkles radiating outward, bright particle bursts, and that triumphant anime glow effect",
        # Determined/Motivated emotions
        (
            "determined",
            "stressed",
        ): "Intense aura effects with energy waves, dramatic wind whipping around character, power-up particle effects, and strong rim lighting",
        (
            "determined",
            "frustrated",
        ): "Crackling energy effects, sharp light rays cutting through darkness, swirling power aura, and dynamic motion blur",
        # Calm/Peaceful emotions
        (
            "contemplative",
            "sad",
        ): "Gentle floating light orbs, soft mist effects, delicate rain droplets, and ethereal god rays breaking through clouds",
        (
            "peaceful",
            "neutral",
        ): "Subtle wind effects, soft particle drift, natural lighting with gentle shadows, and calm atmospheric haze",
        # Sad/Melancholic emotions
        (
            "sad",
            "melancholic",
        ): "Soft rain effects with water droplets on surfaces, muted lighting with gentle shadows, and delicate light particles floating upward",
        (
            "nostalgic",
            "contemplative",
        ): "Golden hour lighting with warm particle effects, soft focus background blur, and gentle memory-like sparkles",
        # Intense/Action emotions
        (
            "intense",
            "focused",
        ): "Sharp contrast lighting, dramatic shadow effects, concentrated energy particles, and powerful atmospheric pressure lines",
        (
            "adventurous",
            "excited",
        ): "Dynamic wind effects, swirling leaves or debris, adventure sparkles, and that epic journey atmosphere",
    }

    # Try to find specific combination
    effect_key = (emotional_tone, mood)
    if effect_key in effect_combinations:
        return effect_combinations[effect_key]

    # Fallback based on emotional tone only
    tone_fallbacks = {
        "happy": "Bright sparkle effects, warm particle glow, gentle wind through hair, and cheerful atmospheric lighting",
        "determined": "Powerful aura effects, energy particles, dramatic wind, and intense lighting with strong shadows",
        "sad": "Soft rain or mist effects, gentle light particles, muted atmospheric glow, and delicate environmental details",
        "contemplative": "Subtle floating particles, soft lighting effects, gentle atmospheric haze, and peaceful environmental elements",
        "excited": "Dynamic particle bursts, energetic sparkles, motion effects, and vibrant atmospheric energy",
        "peaceful": "Calm wind effects, soft particle drift, natural lighting, and serene environmental atmosphere",
        "intense": "Dramatic lighting effects, powerful energy aura, sharp shadows, and intense atmospheric pressure",
        "hopeful": "Uplifting light rays, gentle sparkles rising upward, warm atmospheric glow, and optimistic particle effects",
        "uplifting": "Triumphant light effects, celebratory sparkles, bright atmospheric glow, and joyful particle animation",
    }

    return tone_fallbacks.get(
        emotional_tone,
        "Gentle anime particle effects, soft atmospheric lighting, subtle wind elements, and natural environmental details",
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


def get_anime_style_by_mood(mood: str, vibe: str) -> str:
    """Map user mood and vibe to specific anime visual styles with detailed aesthetic descriptions."""

    # ENHANCED: Detailed anime style mappings with specific visual elements
    anime_styles = {
        # Hopeful & Happy - Slice of Life Aesthetics
        (
            "happy",
            "calm",
        ): "Slice-of-life anime aesthetic with cherry blossom petals floating in warm sunlight, soft cel-shading, pastel color grading, gentle wind effects, and that peaceful afternoon glow typical of healing anime. Think cozy coffee shop scenes with warm golden hour lighting.",
        (
            "happy",
            "adventure",
        ): "Adventure anime style with vibrant sky blues and sunset oranges, dynamic wind-swept hair, sparkling effects in the air, energetic pose lines, and that triumphant hero lighting with lens flares and particle effects dancing around the character.",
        (
            "happy",
            "musical",
        ): "Music anime aesthetic with floating musical notes as light particles, rainbow color gradients, dreamy bokeh effects, stage lighting with colorful spotlights, and that magical performance glow with shimmering background elements.",
        # Stressed & Frustrated - Shonen Battle Aesthetics
        (
            "stressed",
            "motivational",
        ): "Shonen anime battle style with intense orange and red color palette, dramatic speed lines, powerful aura effects radiating from the character, high contrast shadows, and that determined warrior lighting with energy crackling in the background.",
        (
            "frustrated",
            "adventure",
        ): "Dark shonen aesthetic with stormy skies, lightning effects, sharp angular shadows, intense blue and purple color grading, rain droplets, and that epic confrontation atmosphere with wind whipping through the scene.",
        # Sad & Reflective - Emotional Drama Aesthetics
        (
            "sad",
            "calm",
        ): "Emotional drama anime style with soft rain effects, muted blue and gray tones, gentle god rays breaking through clouds, watercolor-like background blur, and that melancholic beauty typical of touching anime moments with subtle light particles.",
        (
            "sad",
            "motivational",
        ): "Inspirational anime aesthetic with a single beam of golden light cutting through darkness, warm amber highlights on the character's face, soft glowing particles rising upward, and that hopeful breakthrough lighting effect.",
        # Neutral & Contemplative - Modern Anime Aesthetics
        (
            "neutral",
            "calm",
        ): "Modern anime style with clean architectural backgrounds, soft natural lighting, realistic shadows, balanced color temperature, and that contemporary urban anime aesthetic with subtle depth of field effects.",
        (
            "neutral",
            "adventure",
        ): "Fantasy anime aesthetic with magical floating particles, ethereal blue and purple lighting, mystical fog effects, enchanted forest atmosphere, and that otherworldly glow with sparkles and light orbs.",
        (
            "neutral",
            "musical",
        ): "Rhythmic anime style with flowing fabric effects, harmonious color transitions, gentle light waves, and that melodic visual flow with soft particle trails following the character's movements.",
        # Additional combinations for richer variety
        (
            "happy",
            "motivational",
        ): "Uplifting shonen style with bright yellow and orange energy aura, triumphant pose effects, victory sparkles, and that champion's glow with radiant background lighting.",
        (
            "stressed",
            "calm",
        ): "Contemplative anime aesthetic with soft blue moonlight, gentle shadow play, peaceful night atmosphere, and that quiet strength lighting with subtle rim lighting effects.",
        (
            "frustrated",
            "motivational",
        ): "Intense transformation anime style with explosive energy effects, dramatic color shifts from dark to bright, power-up aura, and that breakthrough moment lighting with dynamic particle bursts.",
    }

    style_key = (mood, vibe)
    if style_key in anime_styles:
        return anime_styles[style_key]

    # Enhanced fallback descriptions with specific anime visual elements
    mood_fallbacks = {
        "happy": "Bright anime aesthetic with warm golden lighting, cheerful color palette of yellows and pinks, gentle sparkle effects, and that joyful anime glow with soft particle effects.",
        "stressed": "Intense anime style with dramatic red and orange lighting, powerful energy effects, determined expression lines, and that focused warrior atmosphere with dynamic background elements.",
        "frustrated": "Dynamic anime aesthetic with stormy color grading, sharp contrast lighting, intense shadow effects, and that emotional breakthrough atmosphere with swirling energy patterns.",
        "sad": "Gentle anime style with soft blue and purple tones, subtle rain or mist effects, warm rim lighting, and that touching emotional atmosphere with delicate light particles.",
        "neutral": "Balanced anime aesthetic with natural lighting, clean color palette, soft shadows, and that peaceful everyday anime atmosphere with subtle environmental details.",
    }

    return mood_fallbacks.get(
        mood,
        "Beautiful anime style with expressive character animation, vibrant colors, soft cel-shading, and that distinctive anime aesthetic with gentle lighting effects and atmospheric details.",
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
