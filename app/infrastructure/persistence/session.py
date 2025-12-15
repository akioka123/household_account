"""セッション管理"""
from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.persistence.database import AsyncSessionLocal


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """データベースセッションを取得（依存性注入用）"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
