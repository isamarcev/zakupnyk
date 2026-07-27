"""Typed application configuration."""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """App settings; override via environment variables with PROCFLOW_ prefix."""

    model_config = SettingsConfigDict(env_prefix="PROCFLOW_", env_file=".env", extra="ignore")

    data_dir: Path = Path("data")
    host: str = "127.0.0.1"
    port: int = 8077
    open_browser: bool = True  # вимикається в Docker

    @property
    def db_path(self) -> Path:
        return self.data_dir / "procflow.db"

    @property
    def files_dir(self) -> Path:
        return self.data_dir / "files"
