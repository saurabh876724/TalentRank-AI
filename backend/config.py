"""Application configuration loaded from environment variables."""
import os


class Settings:
    APP_TITLE: str = "TalentRank AI API"
    DATABASE_URL: str = os.getenv(
        "TALENTRANK_DATABASE_URL",
        "sqlite:///" + os.path.join(os.path.dirname(__file__), "talentrank.db"),
    )
    MAX_FILE_SIZE_BYTES: int = int(os.getenv("TALENTRANK_MAX_FILE_SIZE", str(5 * 1024 * 1024)))
    MAX_FILES_PER_BATCH: int = int(os.getenv("TALENTRANK_MAX_BATCH", "20"))
    ALLOWED_EXTENSIONS: set[str] = {".pdf", ".docx"}
    CORS_ORIGINS: list[str] = os.getenv(
        "TALENTRANK_CORS_ORIGINS", "http://localhost:3000,http://localhost:5173"
    ).split(",")
    MIN_JD_WORDS: int = 10


settings = Settings()