from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    mongo_uri: str = "mongodb://127.0.0.1:27017"
    mongo_database: str = "computer_store_ai"
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen3:4b-instruct"
    cookie_secure: bool = False
    frontend_origin: str = "http://localhost:5173"
    admin_session_hours: int = Field(default=12, ge=1, le=168)


settings = Settings()
