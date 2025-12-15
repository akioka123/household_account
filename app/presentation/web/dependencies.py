"""依存性注入設定"""
from __future__ import annotations

from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.persistence.session import get_db_session


def get_db() -> AsyncGenerator[AsyncSession, None]:
    """データベースセッションを取得（FastAPI依存性注入用）"""
    return get_db_session()
