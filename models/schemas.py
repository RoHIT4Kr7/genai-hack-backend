from datetime import datetime
from typing import List, Literal, Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator, model_validator
import uuid


class StoryInputs(BaseModel):
    # Core emotional and value-based inputs from new onboarding
    mood: Literal["happy", "stressed", "neutral", "frustrated", "sad"]
    coreValue: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Core value/principle that guides the user",
    )
    supportSystem: str = Field(
        ..., min_length=1, max_length=100, description="Support system type"
    )
    pastResilience: str = Field(
        default="", max_length=500, description="Past challenge that was overcome"
    )
    innerDemon: str = Field(
        default="", max_length=500, description="Main internal struggle"
    )
    desiredOutcome: str = Field(
        default="",
        max_length=500,
        description="Desired outcome after overcoming the struggle",
    )

    # Character identity from new onboarding
    nickname: str = Field(..., min_length=1, max_length=50, description="Hero's name")
    secretWeapon: str = Field(
        default="",
        min_length=1,
        max_length=100,
        description="Secret superpower/strength",
    )
    age: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Age range (teen, young-adult, adult)",
    )
    gender: Literal["female", "male"]

    # Legacy fields (keeping for backward compatibility but making optional)
    vibe: Optional[
        Literal[
            "calm",
            "adventure",
            "musical",
            "motivational",
            "slice-of-life",
            "shonen",
            "isekai",
            "fantasy",
        ]
    ] = None
    archetype: Optional[Literal["mentor", "hero", "companion", "comedian"]] = None
    dream: Optional[str] = None  # Mapped to pastResilience in new onboarding
    mangaTitle: Optional[str] = None
    hobby: Optional[str] = None  # Mapped to secretWeapon in new onboarding

    @field_validator("pastResilience")
    @classmethod
    def validate_past_resilience(cls, v: str) -> str:
        """Provide fallback for empty pastResilience."""
        if not v or not v.strip():
            return "I have overcome challenges before and learned from each experience, building my inner strength."
        return v.strip()

    @field_validator("innerDemon")
    @classmethod
    def validate_inner_demon(cls, v: str) -> str:
        """Provide fallback for empty innerDemon."""
        if not v or not v.strip():
            return "Sometimes I struggle with self-doubt and uncertainty about my path forward."
        return v.strip()

    @field_validator("desiredOutcome")
    @classmethod
    def validate_desired_outcome(cls, v: str) -> str:
        """Provide fallback for empty desiredOutcome."""
        if not v or not v.strip():
            return "I want to feel more confident and at peace with myself, knowing I can handle whatever comes my way."
        return v.strip()

    @field_validator("secretWeapon")
    @classmethod
    def validate_secret_weapon(cls, v: str) -> str:
        """Provide fallback for empty secretWeapon."""
        if not v or not v.strip():
            return "inner strength and determination"
        return v.strip()

    @field_validator("age", mode="before")
    @classmethod
    def validate_age(cls, v) -> str:
        """Convert age from number to string and map to age ranges."""
        if isinstance(v, int):
            # Map numeric age to allowed age ranges
            if v < 18:
                return "teen"
            elif v < 26:
                return "young-adult"
            else:  # 26-35 and above
                return "adult"

        # Validate string values
        if isinstance(v, str) and v in ["teen", "young-adult", "adult"]:
            return v

        # Default fallback
        return "young-adult"

    @model_validator(mode="before")
    @classmethod
    def handle_legacy_fields(cls, values):
        """Handle legacy field names from old frontend versions."""
        if isinstance(values, dict):
            # Map legacy field names to new ones
            if "dream" in values and "pastResilience" not in values:
                values["pastResilience"] = values.get("dream", "")

            if "hobby" in values and "secretWeapon" not in values:
                values["secretWeapon"] = values.get("hobby", "")

            # Ensure required fields have defaults if missing
            if "desiredOutcome" not in values:
                values["desiredOutcome"] = ""

        return values

    @field_validator("vibe", mode="before")
    @classmethod
    def normalize_vibe(cls, v):
        """Coerce free-text or synonymous 'vibe' values to allowed literals.

        Accepts variations like "feeling confident" -> "motivational" and
        gracefully defaults to a safe choice when unrecognized.
        """
        if v is None:
            return None
        try:
            s = str(v).strip().lower()
        except Exception:
            return None

        if not s:
            return None

        # Already valid
        allowed = {
            "calm",
            "adventure",
            "musical",
            "motivational",
            "slice-of-life",
            "shonen",
            "isekai",
            "fantasy",
        }
        if s in allowed:
            return s

        # Map common synonyms/phrases
        if any(
            k in s
            for k in [
                "confident",
                "confidence",
                "strong",
                "motivated",
                "inspired",
                "empowered",
            ]
        ):
            return "motivational"
        if any(
            k in s
            for k in ["calm", "peace", "peaceful", "relaxed", "serene", "tranquil"]
        ):
            return "calm"
        if any(
            k in s
            for k in [
                "adventure",
                "adventurous",
                "explore",
                "journey",
                "quest",
                "travel",
            ]
        ):
            return "adventure"
        if any(
            k in s for k in ["music", "musical", "melody", "song", "sing", "rhythm"]
        ):
            return "musical"
        if any(
            k in s
            for k in ["slice of life", "slice-of-life", "daily", "everyday", "simple"]
        ):
            return "slice-of-life"
        if any(k in s for k in ["shonen", "battle", "fight", "action", "training"]):
            return "shonen"
        if any(
            k in s for k in ["isekai", "other world", "reincarnat", "reborn", "portal"]
        ):
            return "isekai"
        if any(
            k in s for k in ["fantasy", "magical", "magic", "myth", "dragon", "sorcer"]
        ):
            return "fantasy"

        # Fallback safe default
        return "motivational"


class CharacterSheet(BaseModel):
    name: str
    age: str
    appearance: str
    personality: str
    goals: str
    fears: str
    strengths: str


class PropSheet(BaseModel):
    items: List[str]
    environment: str
    lighting: str
    mood_elements: List[str]


class StyleGuide(BaseModel):
    art_style: str
    color_palette: str
    panel_layout: str
    visual_elements: List[str]


class PanelData(BaseModel):
    panel_number: int
    character_sheet: CharacterSheet
    prop_sheet: PropSheet
    style_guide: StyleGuide
    dialogue_text: str
    image_prompt: str
    # music_prompt is optional because current pipeline uses static background music
    music_prompt: Optional[str] = ""
    emotional_tone: str
    # Optional fields produced by services during assembly
    music_url: Optional[str] = None
    tts_text: Optional[str] = None
    # URLs for frontend compatibility (added after workflow completion)
    image_url: Optional[str] = None
    tts_url: Optional[str] = None
    imageUrl: Optional[str] = None  # camelCase for frontend
    narrationUrl: Optional[str] = None  # camelCase for frontend
    backgroundMusicUrl: Optional[str] = None  # camelCase for frontend
    id: Optional[str] = None  # Panel ID for frontend


class GeneratedStory(BaseModel):
    story_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    panels: List[PanelData]
    image_urls: List[str] = Field(default_factory=list)  # GCS URLs
    audio_url: str = ""  # Audio URL (separate background music and TTS files available)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "pending"


class StoryGenerationRequest(BaseModel):
    inputs: StoryInputs


class StoryGenerationResponse(BaseModel):
    story_id: str
    status: str
    message: str
    story: Optional[GeneratedStory] = None


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    services: Dict[str, str]


# Meditation/Dhyaan Models
class MeditationInputs(BaseModel):
    currentFeeling: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="User's current emotional state (sad, upset, anxious, fearful, lonely, guilty, depressed)",
    )
    desiredFeeling: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="What they want to feel (joy, love, peaceful, gratitude, acceptance)",
    )
    experience: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Meditation experience level (beginner, intermediate, advanced)",
    )

    @field_validator("currentFeeling")
    @classmethod
    def validate_current_feeling(cls, v):
        allowed_feelings = [
            "sad",
            "upset",
            "anxious",
            "fearful",
            "lonely",
            "guilty",
            "depressed",
        ]
        if v.lower() not in allowed_feelings:
            raise ValueError(
                f'currentFeeling must be one of: {", ".join(allowed_feelings)}'
            )
        return v.lower()

    @field_validator("desiredFeeling")
    @classmethod
    def validate_desired_feeling(cls, v):
        allowed_feelings = ["joy", "love", "peaceful", "gratitude", "acceptance"]
        if v.lower() not in allowed_feelings:
            raise ValueError(
                f'desiredFeeling must be one of: {", ".join(allowed_feelings)}'
            )
        return v.lower()

    @field_validator("experience")
    @classmethod
    def validate_experience(cls, v):
        allowed_levels = ["beginner", "intermediate", "advanced"]
        if v.lower() not in allowed_levels:
            raise ValueError(f'experience must be one of: {", ".join(allowed_levels)}')
        return v.lower()


class MeditationRequest(BaseModel):
    inputs: MeditationInputs


class MeditationResponse(BaseModel):
    meditation_id: str = Field(..., description="Unique meditation session ID")
    title: str = Field(..., description="Generated meditation title")
    duration: int = Field(..., description="Meditation duration in seconds")
    audio_url: str = Field(..., description="Signed URL for generated meditation audio")
    script: str = Field(..., description="Generated meditation script text")
    background_music_url: str = Field(
        ..., description="Signed URL for background music"
    )
    guidance_type: str = Field(
        ..., description="Type of meditation guidance (breathing, body_scan, etc.)"
    )
    created_at: str = Field(..., description="ISO timestamp of creation")
