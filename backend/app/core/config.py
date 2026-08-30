from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    # AI Router
    AI_PROVIDER: str = "auto"

    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-5"

    # Gemini
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # Groq
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    # Ollama - Local AI
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2:3b"

    # Database
    DATABASE_URL: str = "sqlite:///./reelmind.db"

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000"

    # Files
    UPLOAD_DIR: str = "../uploads"
    OUTPUT_DIR: str = "../outputs"
    MAX_UPLOAD_MB: int = 200

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()