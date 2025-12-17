"""固定費履歴のSQLAlchemy実装"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.port.fixed_item_history_repository import FixedItemHistoryRepository
from app.domain.model.fixed_item_history import FixedItemHistory
from app.domain.model.year_month import YearMonth
from app.infrastructure.persistence.models.fixed_item_history_model import (
    FixedItemHistoryModel,
)


class SqlAlchemyFixedItemHistoryRepository:
    """固定費履歴のSQLAlchemy実装"""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_fixed_item_id(self, fixed_item_id: int) -> list[FixedItemHistory]:
        """固定費項目IDで履歴を取得（適用開始年月順）"""
        stmt = (
            select(FixedItemHistoryModel)
            .where(FixedItemHistoryModel.fixed_item_id == fixed_item_id)
            .order_by(FixedItemHistoryModel.effective_from)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return [self._to_domain(model) for model in models]

    async def find_all(self) -> list[FixedItemHistory]:
        """全固定費履歴を取得"""
        stmt = select(FixedItemHistoryModel).order_by(FixedItemHistoryModel.id)
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return [self._to_domain(model) for model in models]

    async def find_active_at(self, ym: YearMonth) -> list[FixedItemHistory]:
        """指定年月で有効な履歴を取得"""
        ym_str = f"{ym.year:04d}-{ym.month:02d}"
        stmt = select(FixedItemHistoryModel).where(
            FixedItemHistoryModel.effective_from <= ym_str
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        histories = [self._to_domain(model) for model in models]
        # ドメインロジックで有効性をフィルタリング
        return [h for h in histories if h.is_active_at(ym)]

    async def save(self, history: FixedItemHistory) -> None:
        """固定費履歴を保存（新規作成）"""
        ym_str = f"{history.effective_from.year:04d}-{history.effective_from.month:02d}"
        model = FixedItemHistoryModel(
            id=history.id,
            fixed_item_id=history.fixed_item_id,
            effective_from=ym_str,
            amount=history.amount.amount,
            card_id=history.card_id,
            included_in_card=history.included_in_card,
        )
        self._session.add(model)
        await self._session.flush()  # awaitを追加

    def _to_domain(self, model: FixedItemHistoryModel) -> FixedItemHistory:
        """SQLAlchemyモデルをドメインモデルに変換"""
        from app.domain.model.money import Money

        # effective_fromをYearMonthに変換
        year, month = map(int, model.effective_from.split("-"))
        effective_from = YearMonth(year, month)

        return FixedItemHistory(
            id=model.id,
            fixed_item_id=model.fixed_item_id,
            effective_from=effective_from,
            amount=Money(model.amount),
            card_id=model.card_id,
            included_in_card=model.included_in_card,
        )

