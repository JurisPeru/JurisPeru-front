import logging
from functools import lru_cache
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Retrieve(BaseModel):
    k: int = Field(default=15, description="Number of documents to retrieve")
    temperature: float = Field(default=0.5)


class Settings(BaseSettings):
    api_url: str = "http://localhost:8000/api"
    retrieve: Retrieve = Retrieve()
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env.dev",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        env_nested_max_split=1,
    )


@lru_cache
def get_settings():
    return Settings()


def setup_logging():
    settings_local = get_settings()
    level = logging.INFO
    if settings_local.log_level == "ERROR":
        level = logging.ERROR
    elif settings_local.log_level == "DEBUG":
        level = logging.DEBUG

    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler("app.log"), logging.StreamHandler()],
    )
