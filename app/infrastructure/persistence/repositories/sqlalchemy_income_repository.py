"""収入のSQLAlchemy実装"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.port.income_repository import IncomeRepository
from app.domain.model.income import Income
from app.domain.model.year_month import YearMonth
from app.infrastructure.persistence.models.income_model import IncomeModel


class SqlAlchemyIncomeRepository:
    """収入のSQLAlchemy実装"""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert(self, ym: YearMonth, income: Income) -> None:
        """収入を登録または更新"""
        ym_str = ym.to_string()
        stmt = select(IncomeModel).where(IncomeModel.year_month == ym_str)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            # 更新
            model.salary_gross = income.salary_gross.amount
            model.salary_net = income.salary_net.amount
            model.bonus_gross = income.bonus_gross.amount
            model.bonus_net = income.bonus_net.amount
        else:
            # 新規作成
            model = IncomeModel(
                year_month=ym_str,
                salary_gross=income.salary_gross.amount,
                salary_net=income.salary_net.amount,
                bonus_gross=income.bonus_gross.amount,
                bonus_net=income.bonus_net.amount,
            )
            self._session.add(model)

        await self._session.flush()

    async def find(self, ym: YearMonth) -> Income | None:
        """指定年月の収入を取得"""
        ym_str = ym.to_string()
        stmt = select(IncomeModel).where(IncomeModel.year_month == ym_str)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            return None

        return Income.of(
            salary_gross=model.salary_gross,
            salary_net=model.salary_net,
            bonus_gross=model.bonus_gross,
            bonus_net=model.bonus_net,
        )

    async def find_by_year(self, year: int) -> dict[YearMonth, Income]:
        """指定年の全月の収入を取得"""
        year_prefix = f"{year}-"
        stmt = select(IncomeModel).where(IncomeModel.year_month.like(f"{year_prefix}%"))
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        incomes: dict[YearMonth, Income] = {}
        for model in models:
            ym = YearMonth.from_string(model.year_month)
            incomes[ym] = Income.of(
                salary_gross=model.salary_gross,
                salary_net=model.salary_net,
                bonus_gross=model.bonus_gross,
                bonus_net=model.bonus_net,
            )

        return incomes


# Protocol実装として登録
IncomeRepository.register(SqlAlchemyIncomeRepository)
