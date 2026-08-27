"""依存性注入設定"""
from __future__ import annotations

from typing import AsyncIterator

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.persistence.database import AsyncSessionLocal

_SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


async def get_db(request: Request) -> AsyncIterator[AsyncSession]:
    """データベースセッションを取得（FastAPI依存性注入用）

    参照系（GET/HEAD/OPTIONS）は更新を行わないためcommitしない。
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        else:
            if request.method not in _SAFE_METHODS:
                await session.commit()
        # async withが自動的にセッションをクローズする
