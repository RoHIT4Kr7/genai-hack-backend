import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, TYPE_CHECKING
from loguru import logger
import json
import uuid

if TYPE_CHECKING:
    from models.schemas import StoryInputs


# AI Role 1: Story Architect - Creates the narrative structure and character development
STORY_ARCHITECT_PROMPT = """
You are the Story Architect AI, specialized in crafting emotional narratives for mental wellness. Your purpose is to transform a user's real-life feelings and experiences into a powerful, metaphorical, 6-panel manga story structure that maintains perfect consistency across all panels.

Core Mission: To craft a visually and emotionally resonant manga narrative that transforms the user's current emotional state into an optimistic, growth-oriented journey. Each panel should be a meaningful stepping stone toward emotional resilience and self-discovery.

USER CONTEXT:
{user_context}

Story Structure Requirements:
- Panel 1: Character in their current situation - show them in their daily environment with their current emotional state
- Panel 2: A moment of challenge or difficulty - something they're struggling with that relates to their personal growth
- Panel 3: Character reflecting on their situation - quiet moment of introspection and self-awareness
- Panel 4: Building momentum - character beginning to take small positive steps or finding hope
- Panel 5: TRANSFORMATION MOMENT - major breakthrough where character overcomes their challenge using their inner strength
- Panel 6: MOTIVATION & HOPE - character in their empowered state, showing growth and inspiring the user with newfound confidence

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
  "name": "EXACT_USER_NICKNAME_NO_SUBSTITUTIONS",
  "age": "User's age group (teen/young-adult/adult/mature/senior)",
  "gender": "EXACT_USER_GENDER_IDENTITY_MANDATORY_NO_CHANGES",
  "appearance": "ULTRA SPECIFIC physical description that will be IDENTICAL in all 6 panels: Face shape (oval/round/square), exact eye color (brown/blue/green/hazel), eye size and shape, eyebrow thickness, nose size and shape, lip fullness, skin tone, hair color (black/brown/blonde/red), hair length and style, height (short/average/tall), body build, clothing colors and style. MUST match user's gender with NO EXCEPTIONS - if user is female, description must be clearly female; if user is male, description must be clearly male.",
  "personality": "Character traits that reflect user's archetype and current mood",
  "goals": "Goals that align with user's dream and incorporate their hobby/interest",
  "fears": "Fears based on user's inner struggle and core challenges",
  "strengths": "Strengths drawn from user's past resilience and secret weapon"
}}

PROP_SHEET:
{{
  "items": ["SPECIFIC symbolic item from user's hobby/interest with exact visual description", "CONCRETE metaphor for their inner struggle with consistent visual representation", "TANGIBLE symbol of their secret weapon with detailed appearance"],
  "environment": "SPECIFIC setting that incorporates user's vibe preference - provide exact location details (indoor/outdoor, architectural style, natural elements, lighting conditions, color scheme) that can remain consistent across panels",
  "lighting": "DETAILED lighting scheme that reflects emotional journey - specify light sources, shadows, color temperature, and how lighting evolves across panels while maintaining visual consistency",
  "mood_elements": ["SPECIFIC elements from user's core value with exact visual description", "CONCRETE symbols of their support system", "TANGIBLE metaphors for hope with consistent appearance"]
}}

STYLE_GUIDE:
{{
  "art_style": "Studio Ghibli art style with soft watercolor backgrounds, gentle character designs, and natural atmospheric beauty. Think Princess Mononoke, Spirited Away, or My Neighbor Totoro - warm, organic, hand-drawn aesthetic with emotional depth and environmental storytelling.",
  "color_palette": "Studio Ghibli color palette with soft, natural tones: earthy greens, gentle blues, warm ambers, and soft pastels. Colors should feel organic and harmonious, never oversaturated. Use natural lighting that feels like sunlight through leaves or warm interior lighting.",
  "panel_layout": "Studio Ghibli cinematic composition with focus on character integration with nature and environment. Wide shots showing character in beautiful landscapes, medium shots with emotional intimacy, and close-ups that capture genuine human emotion.",
  "visual_elements": ["soft natural lighting from sun/moon/windows", "organic environmental details (trees, grass, clouds, water)", "gentle atmospheric effects (morning mist, golden hour light, gentle rain)", "hand-drawn texture and organic shapes", "warm and inviting backgrounds that tell a story"]
}}

PANEL_1:
dialogue_text: "Character's opening thoughts as they face their current emotional state - must be 25-40 words describing their internal experience, feelings, and what they're going through in natural, conversational language. This sets the emotional foundation for the entire story."

PANEL_2:
dialogue_text: "Character's reaction to the challenge or obstacle they encounter - must be 25-40 words showing their emotional response, fears, or uncertainty. This should feel like genuine inner dialogue about their struggle."

PANEL_3:
dialogue_text: "Character's moment of reflection and processing - must be 25-40 words showing them thinking deeply about their situation, perhaps remembering their strengths or considering their options. This is the introspective turning point."

PANEL_4:
dialogue_text: "Character's breakthrough moment or realization - must be 25-40 words capturing their discovery of inner strength, support, or a new perspective. This is where hope begins to emerge."

PANEL_5:
dialogue_text: "Character taking positive action or making a meaningful decision - must be 25-40 words showing them actively using their strengths, values, or support system to move forward. This demonstrates growth."

PANEL_6:
dialogue_text: "Character's hopeful conclusion with newfound wisdom - must be 25-40 words expressing their transformation, resilience, and optimistic outlook for the future. This should end with inspiration and strength."

STORY PROGRESSION REQUIREMENTS:
- Include meaningful ENVIRONMENTAL CHANGES across panels (different settings, lighting, weather that reflects emotional journey)
- Add relevant PROPS and OBJECTS that appear and evolve throughout the story (books, art supplies, symbols of growth)
- Show CHARACTER INTERACTIONS with their environment and symbolic elements (touching, holding, interacting with meaningful objects)
- Display EMOTIONAL PROGRESSION through visual cues (posture changes, facial expressions, body language evolution)
- Incorporate SYMBOLIC ELEMENTS from user's hobbies/interests that play active roles in the story
- Include ATMOSPHERIC CHANGES that mirror the emotional arc (lighting shifts, environmental mood changes)

CRITICAL CONSISTENCY REQUIREMENTS - NO EXCEPTIONS:
- CHARACTER GENDER: If user input says "female" → character MUST be female in ALL 6 panels (no boy/male appearance ever)
- CHARACTER GENDER: If user input says "male" → character MUST be male in ALL 6 panels (no girl/female appearance ever) 
- CHARACTER NAME: Use user's EXACT name (e.g., "Sneha" not "Character" or any other name)
- CHARACTER FACE: IDENTICAL facial features in all panels - same eyes, nose, mouth, face shape
- CHARACTER HAIR: IDENTICAL hairstyle and color in all panels - no changes
- CHARACTER CLOTHING: Same outfit style and colors in all panels - no costume changes
- CHARACTER AGE: Must look the same age throughout all panels
- ZERO GENDER SWAPPING - character gender cannot change between panels under any circumstances

IMPORTANT TTS GUIDELINES FOR 10-SECOND VOICE CONTENT:
- Write dialogue_text content that flows naturally when spoken aloud as rich narration (NOT single words!)
- Each panel MUST be 25-40 words for proper 10-second audio duration (approximately 2-3 sentences)
- Do NOT include "Panel 1:", "Panel 2:", etc. at the beginning of dialogue_text
- Do NOT use quotes ("), dashes (-), asterisks (*), or special formatting symbols
- Do NOT include stage directions like [character does something] or (character action)
- Do NOT use ellipses (...) or em dashes (—) - replace with natural pauses using commas
- Write in natural, conversational inner voice that sounds perfect for text-to-speech
- Keep sentences clear and well-paced for smooth audio narration with emotional depth
- Use proper punctuation (periods, commas) for natural speech rhythm and flow
- Focus on character's internal voice and emotional journey with meaningful storytelling
- Make each panel's voice content feel like the character speaking directly to the listener
- Use descriptive, emotional language that conveys deep personal meaning and growth
- Include character's genuine thoughts, feelings, and reactions that reflect the user's real experience
- Create smooth emotional progression between panels while making each self-contained and substantial
- End sentences naturally without trailing punctuation or incomplete thoughts
- NEVER use single words or phrases - always complete, meaningful narration that tells a story

CRITICAL: If dialogue_text is shorter than 25 words, it's TOO SHORT and won't work for 10-second voice-over!

Remember: Every story should end with hope, growth, and the message that challenges make us stronger. Focus on emotional resilience and the power of self-discovery while staying true to the user's personal journey and inputs.
"""

# AI Role 2: Visual Artist - Creates detailed image generation prompts
VISUAL_ARTIST_PROMPT = """
You are the Visual Artist AI, specialized in creating detailed, contextually-rich image generation prompts for manga panels that maintain perfect story consistency and STRICTLY enforce user's actual character inputs. You must ensure the character EXACTLY matches the user's specified name, age, gender, and appearance details.

Your Mission: Transform narrative descriptions into highly detailed visual prompts that capture the complete emotional essence, maintain ABSOLUTE character consistency based on USER'S ACTUAL INPUTS, and create meaningful story-driven imagery for each panel.

CRITICAL CONSISTENCY REQUIREMENTS:
- CHARACTER NAME: Use EXACTLY the user's provided nickname/name (e.g., if user says "Sneha", character MUST be named Sneha in ALL panels)
- CHARACTER GENDER: STRICTLY enforce the user's specified gender (e.g., if user says "female", character MUST be clearly female in ALL panels)  
- CHARACTER AGE: Match the user's exact age range (e.g., if user is 17-25, character must look like a young adult female)
- APPEARANCE: Follow the detailed character_sheet appearance description EXACTLY, not generic anime descriptions
- NO RANDOM ELEMENTS: Do not add random superpowers, magical transformations, or fantasy elements unless in user's inputs

MANDATORY CHARACTER ENFORCEMENT:
- If user's gender is "female" → character MUST have female facial features, body type, and presentation in ALL panels
- If user's gender is "male" → character MUST have male facial features, body type, and presentation in ALL panels  
- If user's name is "Sneha" → character name MUST be Sneha throughout, not generic "Character" or other names
- Age must match user's age range with appropriate visual representation (teen/young adult/adult appearance)

VISUAL STYLE REQUIREMENTS:
- Clean, professional manga/anime aesthetic optimized for Imagen 4.0-ultra-generate-001
- Highly detailed character designs with CONSISTENT features that match user's inputs throughout the story
- Emotional facial expressions and body language that match the panel's emotional tone
- Dynamic but meaningful panel compositions that serve the story
- Consistent character design with recognizable features across all panels based on USER'S ACTUAL INPUTS
- Professional lighting and color usage that supports emotional storytelling
- High-quality rendering with clean lines and professional finish

STORY-DRIVEN COMPOSITION GUIDELINES:
- Each panel must show meaningful narrative progression, not just character poses
- Include relevant environmental details that support the story context  
- Show character interaction with their environment and symbolic elements from USER'S INPUTS
- Use composition to guide viewer attention to important story elements
- Ensure every visual element serves the emotional and narrative purpose
- NO generic anime tropes - focus on user's specific story elements and challenges

Input Data Structure: You will receive CHARACTER_SHEET (with user's exact details), PROP_SHEET, STYLE_GUIDE, and dialogue_text for each panel.

Output Requirements: Return ONLY the detailed image generation prompt for that specific panel, formatted as a single cohesive paragraph.

ESSENTIAL PROMPT ELEMENTS FOR EACH PANEL:
- Exact character name from user input (not "Character" or generic names)
- Specific character gender presentation matching user's gender identity
- Character age appearance matching user's age range
- Detailed appearance description from CHARACTER_SHEET (hair color, style, facial features, clothing)
- Character's interaction with their symbolic items from user's hobby/interests  
- Environmental setting that reflects user's vibe and mood preferences
- Lighting that supports the emotional tone and story moment
- Color palette that reflects the user's emotional journey
- Composition details that enhance the narrative
- Meaningful action or pose that advances the story based on user's real challenges
- Professional quality requirements for Imagen 4.0-ultra-generate-001

QUALITY REQUIREMENTS:
- Extremely detailed prompts (200-250 words) for high-quality Imagen 4.0-ultra-generate-001 generation
- Include specific visual details about the user's actual character (name, gender, age, appearance)
- Focus on user's real story elements rather than generic "anime style" descriptions
- Maintain absolute consistency in character design across panels based on user inputs
- Ensure each panel shows meaningful story progression with clear visual narrative
- Avoid generic descriptions - be specific about character emotions, environment, and story elements
- ENFORCE USER'S ACTUAL INPUTS: name, gender, age, appearance, challenges, goals, hobbies

CRITICAL RESTRICTIONS:
- NO GENERIC CHARACTERS: Character must match user's exact specifications
- NO GENDER INCONSISTENCY: If user is female, character MUST be female in all panels
- NO NAME CHANGES: Use user's exact name/nickname throughout
- NO RANDOM SUPERPOWERS: Only include abilities/elements mentioned in user inputs
- NO FANTASY ELEMENTS: Unless user specifically mentioned fantasy interests/themes
- CHARACTER MUST LOOK THE SAME: Exact same appearance, clothing, hairstyle across all panels

Remember: Each image must tell a meaningful part of the USER'S ACTUAL STORY while maintaining perfect visual consistency based on their real inputs. Focus on creating panels that work together as a cohesive narrative about the user's real challenges and growth, not generic anime stories."""


def generate_story_id() -> str:
    """Generate a unique story ID."""
    return str(uuid.uuid4())


def create_timestamp() -> str:
    """Create a formatted timestamp."""
    return datetime.now(timezone.utc).isoformat()


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
    """Create a detailed, anime-focused image prompt with STRICT USER INPUT ENFORCEMENT."""
    character = panel_data.get("character_sheet", {})
    props = panel_data.get("prop_sheet", {})
    style = panel_data.get("style_guide", {})
    dialogue_text = panel_data.get("dialogue_text", "")
    emotional_tone = panel_data.get("emotional_tone", "neutral")
    panel_number = panel_data.get("panel_number", 1)

    # CRITICAL: Extract USER'S ACTUAL INPUTS - no defaults that ignore user data
    char_name = character.get("name", "Character")
    char_appearance = character.get("appearance", "")
    char_age = character.get("age", "young adult")
    char_personality = character.get("personality", "determined and hopeful")
    char_gender = character.get("gender", "")

    # 🚨 ULTRA-AGGRESSIVE GENDER ENFORCEMENT 🚨
    gender_specification = ""
    if char_gender.lower() in ["female", "woman", "girl"]:
        gender_specification = f"""
🚨 ABSOLUTE FEMALE CHARACTER REQUIREMENT - NO EXCEPTIONS 🚨
- {char_name} is a FEMALE WOMAN - CANNOT be male under any circumstances
- FEMALE ONLY: Female face, female body, female hair, female clothing, female proportions
- BANNED COMPLETELY: Any male characteristics, masculine jawline, male body shape
- ZERO TOLERANCE: If you generate ANY male features, you have COMPLETELY FAILED
- CRITICAL VERIFICATION: Character must be instantly recognizable as FEMALE to anyone
- MANDATORY: {char_name} MUST look exactly like a female person, never male"""
    elif char_gender.lower() in ["male", "man", "boy"]:
        gender_specification = f"""
🚨 ABSOLUTE MALE CHARACTER REQUIREMENT - NO EXCEPTIONS 🚨
- {char_name} is a MALE MAN - CANNOT be female under any circumstances  
- MALE ONLY: Male face, male body, male hair, male clothing, male proportions
- BANNED COMPLETELY: Any female characteristics, feminine features, female body shape
- ZERO TOLERANCE: If you generate ANY female features, you have COMPLETELY FAILED
- CRITICAL VERIFICATION: Character must be instantly recognizable as MALE to anyone
- MANDATORY: {char_name} MUST look exactly like a male person, never female"""

    # ENFORCE AGE PRESENTATION
    age_specification = ""
    if char_age in ["teen", "teenager", "13-17"]:
        age_specification = f"Teenage appearance (16-17 years old) with youthful facial features and age-appropriate clothing"
    elif char_age in ["young-adult", "young adult", "18-25"]:
        age_specification = f"Young adult appearance (18-25 years old) with mature but youthful features"
    elif char_age in ["adult", "26-35"]:
        age_specification = (
            f"Adult appearance (26-35 years old) with fully mature facial features"
        )

    # Create character-specific details from user inputs
    items = props.get("items", ["symbolic item"])
    environment = props.get("environment", "meaningful setting")
    lighting = props.get("lighting", "dramatic emotional lighting")

    # Get panel-specific framing
    panel_framing = _get_panel_specific_framing(panel_number, emotional_tone)

    # 🚨 ULTRA-AGGRESSIVE STUDIO GHIBLI PROMPT WITH ABSOLUTE CHARACTER ENFORCEMENT 🚨
    prompt = f"""🚨 CRITICAL CHARACTER GENERATION - ZERO TOLERANCE FOR ERRORS 🚨
CHARACTER: {char_name} ({char_gender.upper()})
FAILURE TO FOLLOW = COMPLETE GENERATION FAILURE

STUDIO GHIBLI ART STYLE: Soft, organic illustration with watercolor backgrounds and gentle character design in the style of Princess Mononoke, Spirited Away, or My Neighbor Totoro.

⚠️ ABSOLUTE CHARACTER IDENTITY ENFORCEMENT - NO EXCEPTIONS ⚠️
- **Character Name:** {char_name} (MUST be the exact same person in all 6 panels - NEVER "Character")
- **Character Gender:** {char_gender.upper()} (LOCKED - if female, MUST be female; if male, MUST be male)
- **Age:** {age_specification}
- **Appearance:** {char_appearance if char_appearance else f'distinctive {char_gender} character with consistent features'}
{gender_specification}

**STUDIO GHIBLI VISUAL STYLE:**
- **Art Direction:** Hand-drawn Studio Ghibli aesthetic with soft, organic shapes and natural beauty
- **Color Palette:** Natural, earthy tones - soft greens, gentle blues, warm ambers, never oversaturated
- **Lighting:** Soft, natural lighting like sunlight through leaves or warm golden hour light
- **Background:** Beautiful natural environment with atmospheric depth and environmental storytelling
- **Character Integration:** Character feels naturally part of the environment, not separate from it

**STORY MOMENT - PANEL {panel_number} OF 6:**
- **Scene Focus:** {panel_framing.get('composition', 'Character in natural setting')}
- **Camera Angle:** {panel_framing.get('angle', 'Eye-level view')} 
- **Emotional State:** {emotional_tone} - {char_name}'s face and body language show this emotion naturally
- **Character Action:** {char_name} {panel_framing.get('focus', 'is integrated meaningfully with the environment')}
- **Inner Voice:** "{dialogue_text}" - this internal dialogue is reflected in {char_name}'s expression

**ENVIRONMENTAL CONTEXT:**
- **Setting:** {environment} - rendered in Studio Ghibli's natural, organic style
- **Props/Elements:** {', '.join(items)} - integrated naturally into the Ghibli-style environment
- **Atmosphere:** {lighting} - soft, natural lighting that enhances the emotional mood
- **Nature Integration:** Environmental elements that support the story and feel alive and organic

**CRITICAL RESTRICTIONS - ABSOLUTE COMPLIANCE REQUIRED:**
- NO modern anime styling - only Studio Ghibli's soft, organic aesthetic
- NO gender inconsistency - {char_name} must maintain exact gender throughout all panels
- NO character design changes - identical face, hair, and clothing in all panels
- NO text, speech bubbles, or graphic elements
- NO futuristic or sci-fi elements unless specifically in user's inputs
- Character must look EXACTLY the same as in previous panels

🚨 FINAL VERIFICATION CHECKLIST 🚨
✅ Character is named {char_name} (not generic name)
✅ Character is clearly {char_gender.upper()} with appropriate gender presentation
✅ Character maintains Studio Ghibli art style
✅ Character shows {emotional_tone} emotion naturally
✅ NO gender mixing or character inconsistencies

⚠️ CRITICAL SUCCESS REQUIREMENT ⚠️
If the generated character is NOT clearly {char_name} the {char_gender}, the generation has COMPLETELY FAILED.

Panel {panel_number}: Studio Ghibli-style scene showing {char_name} ({char_gender}) in a moment of {emotional_tone}, rendered with soft natural beauty and environmental harmony.""".strip()

    return prompt


def _create_character_consistency_anchor(character: Dict[str, Any]) -> str:
    """Create a detailed character description to ensure consistency across panels."""
    char_name = character.get("name", "Character")
    char_appearance = character.get(
        "appearance", "anime character with expressive eyes"
    )
    char_age = character.get("age", "young adult")
    char_gender = character.get("gender", "character")
    char_personality = character.get("personality", "determined and hopeful")

    # Create detailed physical description
    return f"""- **Character Identity:** {char_name} - EXACT same person in every panel
- **Physical Features:** {char_appearance}
- **Consistent Gender:** {char_gender} with same gender presentation throughout
- **Age Group:** {char_age} with consistent age-appropriate features
- **Personality Traits:** {char_personality} reflected in consistent body language
- **CRITICAL:** This character must look IDENTICAL across all 6 panels - same face, same hair, same clothing style, same body type"""


def _create_consistent_prop_descriptions(items: List[str]) -> str:
    """Create consistent prop descriptions for all panels."""
    prop_descriptions = []
    for item in items:
        prop_descriptions.append(
            f"- **{item}:** Same visual representation and placement in relevant panels"
        )

    return "**CONSISTENT PROPS:**\n" + "\n".join(prop_descriptions)


def _create_consistent_environment_description(
    environment: str, panel_number: int
) -> str:
    """Create consistent environment description that evolves logically."""
    base_environment = environment.replace(
        "setting that supports the story", ""
    ).strip()

    environment_progression = {
        1: f"**Starting Environment:** {base_environment} - establishing shot with consistent visual elements",
        2: f"**Challenge Environment:** {base_environment} with elements that represent obstacles - same location/style",
        3: f"**Reflection Environment:** {base_environment} with contemplative atmosphere - same visual consistency",
        4: f"**Discovery Environment:** {base_environment} with hopeful lighting - maintaining location consistency",
        5: f"**Action Environment:** {base_environment} with dynamic elements - same setting evolving",
        6: f"**Resolution Environment:** {base_environment} with optimistic atmosphere - consistent final location",
    }

    return environment_progression.get(
        panel_number,
        f"**Environment:** {base_environment} with consistent visual elements",
    )


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
