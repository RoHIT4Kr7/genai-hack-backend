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
        description="Age range (teen, young-adult, adult, mature, senior, not-specified)",
    )
    gender: Literal["female", "male", "non-binary", "not-specified"]

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
            # Map numeric age to age ranges
            if v < 18:
                return "teen"
            elif v < 26:
                return "young-adult"
            elif v < 36:
                return "adult"
            elif v < 51:
                return "mature"
            else:
                return "senior"
        return str(v) if v else "young-adult"

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
    music_prompt: str
    emotional_tone: str


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
