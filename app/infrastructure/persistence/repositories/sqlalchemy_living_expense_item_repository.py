"""生活費品目のSQLAlchemy実装"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.model.living_expense_item import LivingExpenseItem
from app.domain.model.money import Money
from app.domain.model.year_month import YearMonth
from app.infrastructure.persistence.models.living_expense_item_model import (
    LivingExpenseItemModel,
)
from app.infrastructure.persistence.models.living_expense_model import LivingExpenseModel


class SqlAlchemyLivingExpenseItemRepository:
    """生活費品目のSQLAlchemy実装"""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_living_expense_id(self, living_expense_id: int) -> list[LivingExpenseItem]:
        """指定レシート（親LivingExpense）に紐づく品目を取得"""
        stmt = (
            select(LivingExpenseItemModel)
            .where(LivingExpenseItemModel.living_expense_id == living_expense_id)
            .order_by(LivingExpenseItemModel.id)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return [self._to_domain(model) for model in models]

    async def find_by_year_month(self, ym: YearMonth) -> list[LivingExpenseItem]:
        """指定年月に登録された品目を取得（食費レシートとJOINして絞り込む）"""
        ym_str = f"{ym.year:04d}-{ym.month:02d}"
        stmt = (
            select(LivingExpenseItemModel)
            .join(
                LivingExpenseModel,
                LivingExpenseItemModel.living_expense_id == LivingExpenseModel.id,
            )
            .where(LivingExpenseModel.year_month == ym_str)
            .order_by(LivingExpenseItemModel.id)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return [self._to_domain(model) for model in models]

    async def find_all(self) -> list[LivingExpenseItem]:
        """全品目を取得（採番用）"""
        stmt = select(LivingExpenseItemModel).order_by(LivingExpenseItemModel.id)
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return [self._to_domain(model) for model in models]

    async def save(self, item: LivingExpenseItem) -> None:
        """品目を保存（新規作成または更新）"""
        stmt = select(LivingExpenseItemModel).where(LivingExpenseItemModel.id == item.id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            model.living_expense_id = item.living_expense_id
            model.name = item.name
            model.amount = item.amount.amount
            model.sub_category = item.sub_category
        else:
            model = LivingExpenseItemModel(
                id=item.id,
                living_expense_id=item.living_expense_id,
                name=item.name,
                amount=item.amount.amount,
                sub_category=item.sub_category,
            )
            self._session.add(model)

        await self._session.flush()

    async def delete(self, item_id: int) -> None:
        """品目を削除"""
        stmt = select(LivingExpenseItemModel).where(LivingExpenseItemModel.id == item_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            await self._session.delete(model)
            await self._session.flush()

    async def delete_by_living_expense_id(self, living_expense_id: int) -> None:
        """指定レシートに紐づく品目を全件削除"""
        stmt = select(LivingExpenseItemModel).where(
            LivingExpenseItemModel.living_expense_id == living_expense_id
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        for model in models:
            await self._session.delete(model)
        await self._session.flush()

    def _to_domain(self, model: LivingExpenseItemModel) -> LivingExpenseItem:
        """SQLAlchemyモデルをドメインモデルに変換"""
        return LivingExpenseItem(
            id=model.id,
            living_expense_id=model.living_expense_id,
            name=model.name,
            amount=Money(model.amount),
            sub_category=model.sub_category,
        )
