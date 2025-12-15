"""データベース接続設定"""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from app.infrastructure.persistence.config import get_database_url

# Baseクラス（全モデルの基底クラス）
Base = declarative_base()

# エンジン作成
_engine = create_async_engine(
    get_database_url(),
    echo=False,  # SQLログ出力（開発時はTrueに設定可能）
    future=True,
)

# セッションファクトリ
AsyncSessionLocal = async_sessionmaker(
    _engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_session() -> AsyncSession:
    """非同期セッションを取得（依存性注入用）"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
