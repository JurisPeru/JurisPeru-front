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
        env_file=".env.dev",  # NOTE: cambiar en prod
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        env_nested_max_split=1,
    )


@lru_cache
def get_settings():
    return Settings()
