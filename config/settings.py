import os
from pathlib import Path


# Load environment variables from .env file
def load_env_file():
    """Load environment variables from .env file."""
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    # Remove quotes if present
                    value = value.strip().strip('"').strip("'")
                    os.environ[key] = value


# Load .env file
load_env_file()


class Settings:
    def __init__(self):
        # Vertex AI Configuration - SDK uses GOOGLE_APPLICATION_CREDENTIALS env var automatically
        self.vertex_ai_project_id = os.getenv(
            "VERTEX_AI_PROJECT_ID", "hackathon-472205"
        )
        self.model_name = "gemini-2.5-flash"

        # Gemini API Configuration
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "")

        # Storage Settings
        self.gcs_bucket_name = os.getenv("GCS_BUCKET_NAME", "hackathon-asset-genai")

        # Hardcoded Image Generation Settings
        self.imagen_seed = 42  # Default seed (will be overridden per story)

        # Hardcoded Audio Generation Settings
        self.lyria_model = "lyria-002"  # Uses service account credentials automatically
        self.chirp_model = "chirp-3hd"
        self.chirp_voice_id = (
            "en-US-Chirp3-HD-Charon"  # Replace with actual Chirp API key
        )

        # Hardcoded API Settings
        self.api_host = "0.0.0.0"
        self.api_port = 8000
        self.debug = False

        # Hardcoded CORS Settings
        self.cors_origins = "http://localhost:8501,http://127.0.0.1:8501,http://localhost:8080,http://127.0.0.1:8080"

        # Workflow Settings
        self.max_retries = 3
        self.timeout_seconds = 300

        # Performance Optimization Settings
        self.parallel_panel_stagger_delay = 0.5  # Seconds between panel starts
        self.image_generation_timeout = 90  # Seconds per image
        self.tts_generation_timeout = 30  # Seconds per TTS
        self.max_concurrent_images = 3  # Limit concurrent image generation

    @property
    def cors_origins_list(self) -> list:
        """Get CORS origins as a list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]


settings = Settings()
