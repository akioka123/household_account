"""設定のSQLAlchemy実装"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.port.settings_repository import SettingsRepository
from app.domain.model.settings import Settings
from app.infrastructure.persistence.models.settings_model import SettingsModel


class SqlAlchemySettingsRepository:
    """設定のSQLAlchemy実装"""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find(self) -> Settings:
        """設定を取得（存在しない場合はデフォルト設定を返す）"""
        stmt = select(SettingsModel).where(SettingsModel.id == 1)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            return Settings.default()

        return Settings(
            max_variable_items=model.max_variable_items,
            max_fixed_items=model.max_fixed_items,
        )

    async def save(self, settings: Settings) -> None:
        """設定を保存"""
        stmt = select(SettingsModel).where(SettingsModel.id == 1)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            # 更新
            model.max_variable_items = settings.max_variable_items
            model.max_fixed_items = settings.max_fixed_items
        else:
            # 新規作成
            model = SettingsModel(
                id=1,
                max_variable_items=settings.max_variable_items,
                max_fixed_items=settings.max_fixed_items,
            )
            self._session.add(model)

        self._session.flush()

