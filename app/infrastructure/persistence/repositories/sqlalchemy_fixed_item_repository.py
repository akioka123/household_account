"""固定費項目のSQLAlchemy実装"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.port.fixed_item_repository import FixedItemRepository
from app.domain.model.fixed_item import FixedItem
from app.infrastructure.persistence.models.fixed_item_model import FixedItemModel


class SqlAlchemyFixedItemRepository:
    """固定費項目のSQLAlchemy実装"""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_all(self) -> list[FixedItem]:
        """全固定費項目を取得"""
        stmt = select(FixedItemModel).order_by(FixedItemModel.id)
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return [self._to_domain(model) for model in models]

    async def find_by_id(self, fixed_item_id: int) -> FixedItem | None:
        """IDで固定費項目を取得"""
        stmt = select(FixedItemModel).where(FixedItemModel.id == fixed_item_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            return None

        return self._to_domain(model)

    async def save(self, fixed_item: FixedItem) -> None:
        """固定費項目を保存（新規作成または更新）"""
        stmt = select(FixedItemModel).where(FixedItemModel.id == fixed_item.id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            # 更新
            model.name = fixed_item.name
        else:
            # 新規作成
            model = FixedItemModel(id=fixed_item.id, name=fixed_item.name)
            self._session.add(model)

        self._session.flush()

    def _to_domain(self, model: FixedItemModel) -> FixedItem:
        """SQLAlchemyモデルをドメインモデルに変換"""
        return FixedItem(id=model.id, name=model.name)

