"""依存性注入設定"""
from __future__ import annotations

from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.persistence.session import get_db_session


async def get_db() -> AsyncIterator[AsyncSession]:
    """データベースセッションを取得（FastAPI依存性注入用）"""
    async for session in get_db_session():
        yield session
