"""生活費のSQLAlchemy実装"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.model.living_expense import LivingExpense
from app.domain.model.year_month import YearMonth
from app.infrastructure.persistence.models.living_expense_model import LivingExpenseModel


class SqlAlchemyLivingExpenseRepository:
    """生活費のSQLAlchemy実装"""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_year_month(self, ym: YearMonth) -> list[LivingExpense]:
        """指定年月の生活費を取得"""
        ym_str = f"{ym.year:04d}-{ym.month:02d}"
        stmt = (
            select(LivingExpenseModel)
            .where(LivingExpenseModel.year_month == ym_str)
            .order_by(LivingExpenseModel.id)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return [self._to_domain(model) for model in models]

    async def find_all(self) -> list[LivingExpense]:
        """全生活費を取得"""
        stmt = select(LivingExpenseModel).order_by(LivingExpenseModel.id)
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return [self._to_domain(model) for model in models]

    async def save(self, living_expense: LivingExpense) -> None:
        """生活費を保存（新規作成または更新）"""
        ym_str = f"{living_expense.year_month.year:04d}-{living_expense.year_month.month:02d}"
        stmt = select(LivingExpenseModel).where(LivingExpenseModel.id == living_expense.id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        location_val = living_expense.location if living_expense.location else None

        if model:
            model.year_month = ym_str
            model.category = living_expense.category
            model.location = location_val
            model.amount = living_expense.amount.amount
            model.note = living_expense.note
            model.receipt_image_path = living_expense.receipt_image_path
        else:
            model = LivingExpenseModel(
                id=living_expense.id,
                year_month=ym_str,
                category=living_expense.category,
                location=location_val,
                amount=living_expense.amount.amount,
                note=living_expense.note,
                receipt_image_path=living_expense.receipt_image_path,
            )
            self._session.add(model)

        await self._session.flush()

    async def delete(self, living_expense_id: int) -> None:
        """生活費を削除"""
        stmt = select(LivingExpenseModel).where(LivingExpenseModel.id == living_expense_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            await self._session.delete(model)
            await self._session.flush()

    def _to_domain(self, model: LivingExpenseModel) -> LivingExpense:
        """SQLAlchemyモデルをドメインモデルに変換"""
        from app.domain.model.money import Money

        year, month = map(int, model.year_month.split("-"))
        year_month = YearMonth(year, month)
        location = model.location if model.location is not None else ""

        return LivingExpense(
            id=model.id,
            year_month=year_month,
            category=model.category,
            location=location,
            amount=Money(model.amount),
            note=model.note,
            receipt_image_path=model.receipt_image_path,
        )
