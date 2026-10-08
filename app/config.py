import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Settings:
    crm_base_url: str = os.getenv(
        "CRM_BASE_URL",
        "https://analyst-assessment-production.up.railway.app/api/v1",
    ).rstrip("/")
    crm_api_token: str = os.getenv("CRM_API_TOKEN", "")
    website: str = os.getenv(
        "BELLHAVEN_WEBSITE",
        "https://analyst-assessment-production.up.railway.app",
    ).rstrip("/")
    review_db: str = os.getenv("REVIEW_DB", "review_queue.db")

settings = Settings()
