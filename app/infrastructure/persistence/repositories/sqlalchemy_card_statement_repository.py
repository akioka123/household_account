"""カード請求のSQLAlchemy実装"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.port.card_statement_repository import CardStatementRepository
from app.domain.model.card_statement import CardStatement
from app.domain.model.year_month import YearMonth
from app.infrastructure.persistence.models.card_statement_model import CardStatementModel


class SqlAlchemyCardStatementRepository:
    """カード請求のSQLAlchemy実装"""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_year_month(self, ym: YearMonth) -> list[CardStatement]:
        """指定年月のカード請求を取得"""
        ym_str = f"{ym.year:04d}-{ym.month:02d}"
        stmt = select(CardStatementModel).where(CardStatementModel.year_month == ym_str)
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return [self._to_domain(model) for model in models]

    async def find_all(self) -> list[CardStatement]:
        """全カード請求を取得"""
        stmt = select(CardStatementModel).order_by(CardStatementModel.id)
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return [self._to_domain(model) for model in models]

    async def save(self, statement: CardStatement) -> None:
        """カード請求を保存（新規作成または更新）"""
        ym_str = f"{statement.year_month.year:04d}-{statement.year_month.month:02d}"
        stmt = select(CardStatementModel).where(
            CardStatementModel.year_month == ym_str,
            CardStatementModel.card_id == statement.card_id,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            # 更新
            model.amount = statement.amount.amount
        else:
            # 新規作成
            model = CardStatementModel(
                id=statement.id,
                year_month=ym_str,
                card_id=statement.card_id,
                amount=statement.amount.amount,
            )
            self._session.add(model)

        self._session.flush()

    async def delete(self, statement_id: int) -> None:
        """カード請求を削除"""
        stmt = select(CardStatementModel).where(CardStatementModel.id == statement_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            self._session.delete(model)
            self._session.flush()

    def _to_domain(self, model: CardStatementModel) -> CardStatement:
        """SQLAlchemyモデルをドメインモデルに変換"""
        from app.domain.model.money import Money

        # year_monthをYearMonthに変換
        year, month = map(int, model.year_month.split("-"))
        year_month = YearMonth(year, month)

        return CardStatement(
            id=model.id,
            year_month=year_month,
            card_id=model.card_id,
            amount=Money(model.amount),
        )

