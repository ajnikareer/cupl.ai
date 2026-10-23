import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_ENV: str = "live"
    GCP_PROJECT: str = ""
    VERTEX_LOCATION: str = "us-central1"
    FIRESTORE_DB: str = "(default)"
    ALLOWED_ORIGINS: str = "http://localhost:5173"
    APP_PUBLIC_URL: str = "http://localhost:5173"
    APP_TZ: str = "Asia/Kolkata"
    PORT: int = 8080

    GEMINI_LIVE_MODEL: str = "gemini-live-2.5-flash-native-audio"
    GEMINI_AGENT_MODEL: str = "gemini-2.5-flash"
    GEMINI_PLANNER_MODEL: str = "gemini-2.5-pro"
    GEMINI_FAST_MODEL: str = "gemini-2.5-flash"
    GEMINI_EMBED_MODEL: str = "gemini-embedding-001"
    EMBED_DIM: int = 768
    AGENT_THINKING_BUDGET: int = 0

    LIVE_VOICE_NAME: str = "Aoede"
    LIVE_LANGUAGE: str = ""
    LIVE_AFFECTIVE_DIALOG: bool = True
    LIVE_PROACTIVE_AUDIO: bool = True
    LIVE_START_SENSITIVITY: str = "HIGH"
    LIVE_END_SENSITIVITY: str = "LOW"
    LIVE_SILENCE_MS: int = 700
    LIVE_PREFIX_PADDING_MS: int = 150

    QLOO_BASE_URL: str = "https://hackathon.api.qloo.com"
    QLOO_API_KEY: str = ""
    QLOO_TIMEOUT_S: float = 8.0
    QLOO_CACHE_TTL_H: int = 24
    DEFAULT_REGION: str = "India"

    AGENT_TOOL_TRANSPORT: str = "mcp"
    MCP_URL: str = ""
    MCP_INTERNAL_TOKEN: str = ""

    LEARN_EVERY_N_TURNS: int = 4
    CRON_SECRET: str = ""

    @property
    def origins(self) -> list[str]:
        return [o.strip().rstrip("/") for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]

    @property
    def mcp_url(self) -> str:
        return self.MCP_URL or f"http://127.0.0.1:{self.PORT}/mcp/"


settings = Settings()


def startup_guard() -> None:
    """Live environment never runs with demo flags, missing keys or a weak MCP token."""
    if settings.APP_ENV == "live":
        demo = [k for k in os.environ if k.upper().startswith("DEMO_")]
        if demo:
            raise RuntimeError(f"APP_ENV=live but demo variables present: {demo}")
    if not settings.GCP_PROJECT:
        raise RuntimeError("GCP_PROJECT is required")
    if not settings.QLOO_API_KEY or settings.QLOO_API_KEY.startswith("PUT_"):
        raise RuntimeError("QLOO_API_KEY is required (live product, no mock fallback)")
    if len(settings.MCP_INTERNAL_TOKEN) < 16 or settings.MCP_INTERNAL_TOKEN.startswith("change-me"):
        raise RuntimeError("MCP_INTERNAL_TOKEN must be a long random secret")
