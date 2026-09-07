import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Karnataka Electoral Notice Checker"
    SOURCE_URL: str = os.getenv("SOURCE_URL", "https://ceo.karnataka.gov.in/notices_issued.html")
    DISCOVERY_DISTRICT: str = os.getenv("DISCOVERY_DISTRICT", "ALL")
    # Ensure absolute path to database file in project root
    _db_path: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "epic_notice_checker.db"))
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{_db_path}")
    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "admin123")
    OCR_ENABLED: bool = os.getenv("OCR_ENABLED", "true").lower() == "true"
    CRAWLER_TIMEOUT: int = int(os.getenv("CRAWLER_TIMEOUT", "30"))
    DISCOVERY_BATCH_SIZE: int = int(os.getenv("DISCOVERY_BATCH_SIZE", "10"))
    PDF_BATCH_SIZE: int = int(os.getenv("PDF_BATCH_SIZE", "10"))
    DISCOVERY_WORKERS: int = int(os.getenv("DISCOVERY_WORKERS", "2"))
    PDF_WORKERS: int = int(os.getenv("PDF_WORKERS", "4"))
    MAX_PDF_SIZE_MB: int = int(os.getenv("MAX_PDF_SIZE_MB", "50"))
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
    SECRET_KEY: str = os.getenv("SECRET_KEY", "epic-checker-secret-key-2026")
    
    # Celery configuration
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND_URL: str = os.getenv("CELERY_RESULT_BACKEND_URL", "redis://localhost:6379/1")
    
    # Retry policy
    MAX_RETRY_ATTEMPTS: int = int(os.getenv("MAX_RETRY_ATTEMPTS", "5"))
    INITIAL_RETRY_DELAY: int = int(os.getenv("INITIAL_RETRY_DELAY", "5"))  # seconds

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
