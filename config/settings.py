import os
from pathlib import Path
from typing import Optional
from loguru import logger


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
                    # Remove quotes and all whitespace characters (including \r\n)
                    value = value.strip().strip('"').strip("'").strip()
                    os.environ[key] = value


# Load .env file
load_env_file()


# Secret Manager integration for Cloud Run
def get_secret(secret_name: str, project_id: str = None) -> Optional[str]:
    """Get secret from Google Secret Manager or environment variable.

    Falls back to environment variables for local development.
    """
    # First try environment variable (for local development)
    env_value = os.getenv(secret_name.upper().replace("-", "_"))
    if env_value:
        # Clean the environment value of any unwanted whitespace
        return env_value.strip()

    # Try Secret Manager for Cloud Run
    try:
        from google.cloud import secretmanager

        if not project_id:
            project_id = os.getenv("VERTEX_AI_PROJECT_ID", "hackathon-472205")

        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        # Clean the secret value of any unwanted whitespace
        return response.payload.data.decode("UTF-8").strip()

    except Exception as e:
        logger.warning(
            f"Could not fetch secret '{secret_name}' from Secret Manager: {e}"
        )
        return None


def _sanitize(s: str) -> str:
    """Remove CRLF, LF, and hidden whitespace from configuration values."""
    if s is None:
        return ""
    return s.replace("\r", "").replace("\n", "").strip()


def setup_service_account_credentials():
    """Set up service account credentials from Secret Manager for GCS operations."""
    try:
        service_account_json = get_secret("service-account-key")
        if service_account_json:
            import tempfile
            import json
            from google.oauth2 import service_account

            # Write the service account key to a temporary file
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False
            ) as f:
                f.write(service_account_json)
                temp_file_path = f.name

            # Set the environment variable for Google Cloud SDK
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = temp_file_path
            logger.info("✅ Service account credentials loaded from Secret Manager")
            return True
    except Exception as e:
        logger.warning(f"Could not set up service account credentials: {e}")

    return False


class Settings:
    def __init__(self):
        # Vertex AI Configuration - SDK uses GOOGLE_APPLICATION_CREDENTIALS env var automatically
        self.vertex_ai_project_id = os.getenv(
            "VERTEX_AI_PROJECT_ID", "hackathon-472205"
        )
        self.model_name = "gemini-2.5-flash"

        # Gemini API Configuration - Prioritize Secret Manager over environment variables
        self.gemini_api_key = get_secret("gemini-api-key") or os.getenv(
            "GEMINI_API_KEY", ""
        )

        # Log Gemini API key source for debugging
        if get_secret("gemini-api-key"):
            logger.info("Using Gemini API key from Secret Manager")
        elif os.getenv("GEMINI_API_KEY"):
            logger.info("Using Gemini API key from environment variable")
        else:
            logger.warning(
                "No Gemini API key found in Secret Manager or environment variables"
            )

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

        # API Settings - Use dynamic port for Cloud Run
        self.api_host = "0.0.0.0"
        self.api_port = int(os.getenv("PORT", "8000"))  # Cloud Run provides PORT
        # Allow enabling debug mode via env for local development
        self.debug = os.getenv("DEBUG", "false").strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }

        # CORS Settings - Check environment for production URLs
        default_cors = (
            "http://localhost:5173,http://127.0.0.1:5173,"
            "http://localhost:8501,http://127.0.0.1:8501,"
            "http://localhost:8080,http://127.0.0.1:8080,"
            "http://localhost:3000,http://127.0.0.1:3000,"
            "http://localhost:4173,http://127.0.0.1:4173,"
            "http://localhost:8000,http://127.0.0.1:8000,"
            "ws://localhost:8000,ws://127.0.0.1:8000,"
            "ws://localhost:8080,ws://127.0.0.1:8080,"
            "http://localhost,https://localhost,"
            "https://hackathon-472205.el.r.appspot.com,"
            "https://calmira-ai-1.web.app,"
            "https://calmira-ai-1.web.app/"
        )

        self.cors_origins = os.getenv("CORS_ORIGINS", default_cors)

        # Workflow Settings
        self.max_retries = 3
        self.timeout_seconds = 300

        # Performance Optimization Settings
        self.parallel_panel_stagger_delay = 0.5  # Seconds between panel starts
        self.image_generation_timeout = 90  # Seconds per image
        self.tts_generation_timeout = 30  # Seconds per TTS
        self.max_concurrent_images = 3  # Limit concurrent image generation

        # Auth settings - Prioritize Secret Manager for sensitive data
        # Use Secret Manager first, then fall back to environment variables
        raw_secret = get_secret("google-client-id")
        raw_env = os.getenv("GOOGLE_CLIENT_ID", "")

        # Prefer secret over env var, then sanitize
        self.google_client_id = _sanitize(raw_secret or raw_env)

        # Log Client ID source for debugging
        if raw_secret:
            logger.info("Using Google Client ID from Secret Manager")
        elif raw_env:
            logger.info("Using Google Client ID from environment variable")
        else:
            logger.warning(
                "No Google Client ID found in Secret Manager or environment variables"
            )

        # STARTUP LOGGING: Immediately reveal any hidden characters
        print(f"[STARTUP] Google Client ID loaded: {repr(self.google_client_id)}")
        print(f"[STARTUP] Client ID length: {len(self.google_client_id)}")

        # Check for CRLF contamination without backslashes in f-string
        has_crlf = "\r" in repr(self.google_client_id) or "\n" in repr(
            self.google_client_id
        )
        print(f"[STARTUP] Has CRLF contamination: {has_crlf}")

        print(
            f"[STARTUP] Raw secret source: {repr(raw_secret) if raw_secret else 'None (fallback to env)'}"
        )
        print(f"[STARTUP] Raw env source: {repr(raw_env) if raw_env else 'None'}")

        # JWT Secret - Prioritize Secret Manager
        self.jwt_secret_key = get_secret("jwt-secret-key") or os.getenv(
            "JWT_SECRET_KEY", "change-me-in-prod"
        )

        # Log JWT secret source for debugging
        if get_secret("jwt-secret-key"):
            logger.info("Using JWT secret from Secret Manager")
        elif os.getenv("JWT_SECRET_KEY"):
            logger.info("Using JWT secret from environment variable")
        else:
            logger.warning(
                "Using default JWT secret - should be configured in production"
            )
        self.jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        # Minutes (1 week = 7 days * 24 hours * 60 minutes = 10,080 minutes)
        self.jwt_expires_minutes = int(os.getenv("JWT_EXPIRES_MIN", "10080"))

        # Database URL - Prioritize Secret Manager over environment variables
        db_secret = get_secret("database-url")
        db_env = os.getenv("DATABASE_URL")

        self.database_url = (
            db_secret
            or db_env
            or "postgresql://postgres:RoHIT%400192@db.adnrxgcytqchbsnnxcms.supabase.co:5432/postgres"
        )

        # Log database URL source for debugging
        if db_secret:
            logger.info("Using database URL from Secret Manager")
        elif db_env:
            logger.info("Using database URL from environment variable")
        else:
            logger.info("Using default database URL")

        # Setup service account credentials for GCS operations
        setup_service_account_credentials()

    @property
    def cors_origins_list(self) -> list:
        """Get CORS origins as a list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]


settings = Settings()
