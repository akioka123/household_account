"""データベース設定"""

from __future__ import annotations

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# プロジェクトルートを取得（このファイルから見て2階層上）
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
ENV_FILE = PROJECT_ROOT / ".env"


class DatabaseSettings(BaseSettings):
    """データベース接続設定"""

    db_host: str = "db"
    db_port: int = 5432
    db_user: str = "household"
    db_password: str = "secret"
    db_name: str = "household"

    model_config = SettingsConfigDict(
        case_sensitive=False,
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        env_ignore_empty=True,
    )


_settings = DatabaseSettings()


def get_database_url() -> str:
    """データベース接続URLを取得"""
    return (
        f"postgresql+asyncpg://{_settings.db_user}:{_settings.db_password}"
        f"@{_settings.db_host}:{_settings.db_port}/{_settings.db_name}"
    )
