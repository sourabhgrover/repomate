"""Central app configuration, sourced entirely from environment / .env.

Never hardcode API keys or connection strings here or anywhere else, including in
examples or tests (CLAUDE.md coding convention). Loaded once via get_settings() and
injected everywhere through dependencies.py.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    mongodb_uri: str
    mongodb_db_name: str = "repomate_lite"

    embedding_model_name: str = "BAAI/bge-small-en-v1.5"

    llm_provider: str
    llm_model_name: str
    llm_api_key: str

    github_token: str | None = None

    # Demo repo size cap (CLAUDE.md: "~100-150 files"); enforced by FileWalker, not just documented.
    max_repo_files: int = 150

    app_env: str = "development"


@lru_cache
def get_settings() -> Settings:
    ...
