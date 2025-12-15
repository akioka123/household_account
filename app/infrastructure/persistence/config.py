"""データベース設定"""
from __future__ import annotations

import os

from pydantic_settings import BaseSettings


class DatabaseSettings(BaseSettings):
    """データベース接続設定"""

    db_host: str = "db"
    db_port: int = 5432
    db_user: str = "household"
    db_password: str = "secret"
    db_name: str = "household"

    class Config:
        env_prefix = "DB_"
        case_sensitive = False


_settings = DatabaseSettings()


def get_database_url() -> str:
    """データベース接続URLを取得"""
    return (
        f"postgresql+asyncpg://{_settings.db_user}:{_settings.db_password}"
        f"@{_settings.db_host}:{_settings.db_port}/{_settings.db_name}"
    )
