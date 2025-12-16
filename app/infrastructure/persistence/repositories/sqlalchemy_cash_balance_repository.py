"""月初現金のSQLAlchemy実装"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.port.cash_balance_repository import CashBalanceRepository
from app.domain.model.cash_balance import CashBalance
from app.domain.model.year_month import YearMonth
from app.infrastructure.persistence.models.cash_balance_model import CashBalanceModel


class SqlAlchemyCashBalanceRepository:
    """月初現金のSQLAlchemy実装"""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find(self, ym: YearMonth) -> CashBalance | None:
        """指定年月の月初現金を取得"""
        ym_str = f"{ym.year:04d}-{ym.month:02d}"
        stmt = select(CashBalanceModel).where(CashBalanceModel.year_month == ym_str)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            return None

        return self._to_domain(model)

    async def find_all(self) -> list[CashBalance]:
        """全月初現金を取得"""
        stmt = select(CashBalanceModel).order_by(CashBalanceModel.id)
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return [self._to_domain(model) for model in models]

    async def save(self, balance: CashBalance) -> None:
        """月初現金を保存（新規作成または更新）"""
        ym_str = f"{balance.year_month.year:04d}-{balance.year_month.month:02d}"
        stmt = select(CashBalanceModel).where(CashBalanceModel.year_month == ym_str)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            # 更新
            model.amount = balance.amount.amount
        else:
            # 新規作成
            model = CashBalanceModel(
                id=balance.id,
                year_month=ym_str,
                amount=balance.amount.amount,
            )
            self._session.add(model)

        self._session.flush()

    def _to_domain(self, model: CashBalanceModel) -> CashBalance:
        """SQLAlchemyモデルをドメインモデルに変換"""
        from app.domain.model.money import Money

        # year_monthをYearMonthに変換
        year, month = map(int, model.year_month.split("-"))
        year_month = YearMonth(year, month)

        return CashBalance(
            id=model.id,
            year_month=year_month,
            amount=Money(model.amount),
        )
