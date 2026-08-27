"""生活費品目の永続化Port"""
from __future__ import annotations

from typing import Protocol

from app.domain.model.living_expense_item import LivingExpenseItem
from app.domain.model.year_month import YearMonth


class LivingExpenseItemRepository(Protocol):
    """生活費品目の永続化Port"""

    async def find_by_living_expense_id(self, living_expense_id: int) -> list[LivingExpenseItem]:
        """指定レシート（親LivingExpense）に紐づく品目を取得"""
        ...

    async def find_by_year_month(self, ym: YearMonth) -> list[LivingExpenseItem]:
        """指定年月に登録された品目を取得（食費レシートとJOINして絞り込む）"""
        ...

    async def find_all(self) -> list[LivingExpenseItem]:
        """全品目を取得（採番用。IDはレシートをまたいで一意なため全体を見る必要がある）"""
        ...

    async def save(self, item: LivingExpenseItem) -> None:
        """品目を保存（新規作成または更新）"""
        ...

    async def delete(self, item_id: int) -> None:
        """品目を削除"""
        ...

    async def delete_by_living_expense_id(self, living_expense_id: int) -> None:
        """指定レシートに紐づく品目を全件削除"""
        ...
