"""生活費の永続化Port"""
from __future__ import annotations

from typing import Protocol

from app.domain.model.living_expense import LivingExpense
from app.domain.model.year_month import YearMonth


class LivingExpenseRepository(Protocol):
    """生活費の永続化Port"""

    async def find_by_year_month(self, ym: YearMonth) -> list[LivingExpense]:
        """指定年月の生活費を取得"""
        ...

    async def find_all(self) -> list[LivingExpense]:
        """全生活費を取得"""
        ...

    async def save(self, living_expense: LivingExpense) -> None:
        """生活費を保存（新規作成または更新）"""
        ...

    async def delete(self, living_expense_id: int) -> None:
        """生活費を削除"""
        ...
