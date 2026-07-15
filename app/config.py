import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./app.db")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    # Read CORS origins comma-separated string as a list
    CORS_ORIGINS_RAW: str = os.getenv("CORS_ORIGINS", "http://localhost:5173")
    @property
    def CORS_ORIGINS(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS_RAW.split(",") if origin.strip()]
        
    DATA_DIR: str = os.getenv("DATA_DIR", "./data/seoul")

settings = Settings()
