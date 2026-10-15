import json
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    gemini_api_key: Optional[str] = Field(default=None, alias="GEMINI_API_KEY")
    supabase_url: Optional[str] = Field(default=None, alias="SUPABASE_URL")
    supabase_key: Optional[str] = Field(default=None, alias="SUPABASE_KEY")
    
    # We parse the string JSON if it's a string, or default
    cors_origins: str = Field(default='["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:5174"]', alias="CORS_ORIGINS")

    @property
    def cors_origins_list(self) -> List[str]:
        try:
            return json.loads(self.cors_origins)
        except Exception:
            return [x.strip() for x in self.cors_origins.split(",") if x.strip()]

settings = Settings()
