"""カードのSQLAlchemy実装"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.port.card_repository import CardRepository
from app.domain.model.card import Card
from app.infrastructure.persistence.models.card_model import CardModel


class SqlAlchemyCardRepository:
    """カードのSQLAlchemy実装"""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_all(self) -> list[Card]:
        """全カードを取得"""
        stmt = select(CardModel).order_by(CardModel.id)
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return [self._to_domain(model) for model in models]

    async def find_by_id(self, card_id: int) -> Card | None:
        """IDでカードを取得"""
        stmt = select(CardModel).where(CardModel.id == card_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            return None

        return self._to_domain(model)

    async def save(self, card: Card) -> None:
        """カードを保存（新規作成または更新）"""
        stmt = select(CardModel).where(CardModel.id == card.id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            # 更新
            model.name = card.name
            model.enabled = card.enabled
        else:
            # 新規作成
            model = CardModel(id=card.id, name=card.name, enabled=card.enabled)
            self._session.add(model)

        await self._session.flush()

    async def delete(self, card_id: int) -> None:
        """カードを削除"""
        stmt = select(CardModel).where(CardModel.id == card_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            self._session.delete(model)
            await self._session.flush()

    def _to_domain(self, model: CardModel) -> Card:
        """SQLAlchemyモデルをドメインモデルに変換"""
        return Card(id=model.id, name=model.name, enabled=model.enabled)

