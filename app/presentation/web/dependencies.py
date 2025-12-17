"""依存性注入設定"""
from __future__ import annotations

from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.persistence.database import AsyncSessionLocal


async def get_db() -> AsyncIterator[AsyncSession]:
    """データベースセッションを取得（FastAPI依存性注入用）"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        else:
            await session.commit()
        # async withが自動的にセッションをクローズする
