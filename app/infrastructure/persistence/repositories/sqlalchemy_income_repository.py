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
        # LIKEクエリのため、年をパディングしてプレフィックスを作成
        # ただし、to_string()は年をパディングしないため、ここでは明示的にパディング
        # 既存のデータベースレコードとの互換性のため、年はパディングする
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

    async def find_by_years(self, start_year: int, end_year: int) -> dict[YearMonth, Income]:
        """指定期間の全月の収入を取得"""
        from sqlalchemy import and_

        # 年範囲でクエリを作成
        start_prefix = f"{start_year}-"
        end_prefix = f"{end_year}-"
        
        # 年範囲の条件を作成（文字列比較で範囲を指定）
        stmt = select(IncomeModel).where(
            and_(
                IncomeModel.year_month >= start_prefix,
                IncomeModel.year_month < f"{end_year + 1}-"
            )
        ).order_by(IncomeModel.year_month)
        
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        incomes: dict[YearMonth, Income] = {}
        for model in models:
            ym = YearMonth.from_string(model.year_month)
            # 範囲内の年のみを対象とする
            if start_year <= ym.year <= end_year:
                incomes[ym] = Income.of(
                    salary_gross=model.salary_gross,
                    salary_net=model.salary_net,
                    bonus_gross=model.bonus_gross,
                    bonus_net=model.bonus_net,
                )

        return incomes

