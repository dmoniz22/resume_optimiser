from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://resume_user:resume_pass@postgres:5432/resume_optimizer"
    REDIS_URL: str = "redis://valkey:6379/0"

    # Ollama Cloud
    OLLAMA_CLOUD_API_KEY: str = ""
    OLLAMA_CLOUD_BASE_URL: str = "https://ollama.cloud/api/v1"
    AI_MODEL_REWRITE: str = "gemma4:31b"
    AI_MODEL_PARSE: str = "deepseek-v4-flash"
    AI_MODEL_EXTRACT: str = "ministral-3:14b"
    AI_MODEL_COVER_LETTER: str = "gemma4:31b"

    # Local Ollama (embeddings)
    LOCAL_OLLAMA_URL: str = "http://ollama:11434/v1"
    EMBEDDING_MODEL: str = "nomic-embed-text"

    # Stripe
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PRICE_PRO: str = ""
    STRIPE_PRICE_CAREER: str = ""

    # Auth
    JWT_SECRET: str = "change-me-in-production"
    NEXTAUTH_SECRET: str = "change-me-in-production"
    NEXTAUTH_URL: str = "http://localhost:3000"

    # Email
    RESEND_API_KEY: str = ""
    EMAIL_FROM: str = "noreply@resume-optimizer.com"

    # Storage
    UPLOAD_DIR: str = "/data/resumes"

    # Internal
    INTERNAL_API_KEY: str = "change-me-in-production"

    # App
    NEXT_PUBLIC_API_URL: str = "http://localhost:8000/api"
    NEXT_PUBLIC_APP_URL: str = "http://localhost:3000"
    DOMAIN: str = "localhost"


settings = Settings()
