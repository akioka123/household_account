"""生活費管理ユースケース"""
from __future__ import annotations

from dataclasses import dataclass

from app.application.port.living_expense_repository import LivingExpenseRepository
from app.application.port.logger import Logger
from app.domain.model.living_expense import (
    LIVING_EXPENSE_CATEGORY_FOOD,
    LIVING_EXPENSE_CATEGORIES,
    LivingExpense,
)
from app.domain.model.log_context import LogContext
from app.domain.model.money import Money
from app.domain.model.year_month import YearMonth


@dataclass(frozen=True)
class AddLivingExpenseCommand:
    """生活費追加コマンド"""

    year: int
    """年"""
    month: int
    """月"""
    category: str
    """カテゴリ"""
    location: str
    """場所（食費のときのみ必須）"""
    amount: int
    """金額"""
    note: str
    """メモ"""


@dataclass(frozen=True)
class UpdateLivingExpenseCommand:
    """生活費更新コマンド"""

    living_expense_id: int
    """生活費ID"""
    year: int
    """年"""
    month: int
    """月"""
    category: str
    """カテゴリ"""
    location: str
    """場所"""
    amount: int
    """金額"""
    note: str
    """メモ"""


@dataclass(frozen=True)
class DeleteLivingExpenseCommand:
    """生活費削除コマンド"""

    living_expense_id: int
    """生活費ID"""


@dataclass(frozen=True)
class LivingExpenseData:
    """生活費データ（表示用）"""

    by_category: dict[str, list[LivingExpense]]
    """カテゴリ別一覧（表示順は LIVING_EXPENSE_CATEGORIES）"""
    totals_by_category: dict[str, Money]
    """カテゴリ別合計"""


class ManageLivingExpensesUseCase:
    """生活費管理ユースケース"""

    def __init__(
        self,
        living_expense_repo: LivingExpenseRepository,
        logger: Logger,
    ) -> None:
        self._living_expense_repo = living_expense_repo
        self._logger = logger

    async def add_living_expense(self, command: AddLivingExpenseCommand) -> None:
        """生活費を追加

        Args:
            command: 生活費追加コマンド

        Raises:
            ValueError: 食費で場所が空の場合
        """
        if command.category == LIVING_EXPENSE_CATEGORY_FOOD and not (command.location or "").strip():
            raise ValueError("食費の場合は場所が必須です")

        ym = YearMonth(command.year, command.month)
        location = (command.location or "").strip()

        all_expenses = await self._living_expense_repo.find_all()
        next_id = max([e.id for e in all_expenses], default=0) + 1

        living_expense = LivingExpense(
            id=next_id,
            year_month=ym,
            category=command.category,
            location=location,
            amount=Money(command.amount),
            note=command.note or "",
        )

        await self._living_expense_repo.save(living_expense)

        context = LogContext(
            screen="month",
            context={
                "year": command.year,
                "month": command.month,
                "action": "add_living_expense",
            },
        )
        self._logger.info(
            f"生活費追加: {command.year}年{command.month}月 ({command.category}, {command.amount}円)",
            context,
        )

    async def update_living_expense(self, command: UpdateLivingExpenseCommand) -> None:
        """生活費を更新

        Args:
            command: 生活費更新コマンド

        Raises:
            ValueError: 食費で場所が空の場合
        """
        if command.category == LIVING_EXPENSE_CATEGORY_FOOD and not (command.location or "").strip():
            raise ValueError("食費の場合は場所が必須です")

        ym = YearMonth(command.year, command.month)
        location = (command.location or "").strip()

        living_expense = LivingExpense(
            id=command.living_expense_id,
            year_month=ym,
            category=command.category,
            location=location,
            amount=Money(command.amount),
            note=command.note or "",
        )

        await self._living_expense_repo.save(living_expense)

        context = LogContext(
            screen="month",
            context={
                "year": command.year,
                "month": command.month,
                "action": "update_living_expense",
                "living_expense_id": command.living_expense_id,
            },
        )
        self._logger.info(
            f"生活費更新: ID {command.living_expense_id} ({command.category}, {command.amount}円)",
            context,
        )

    async def delete_living_expense(self, command: DeleteLivingExpenseCommand) -> None:
        """生活費を削除

        Args:
            command: 生活費削除コマンド
        """
        await self._living_expense_repo.delete(command.living_expense_id)

        context = LogContext(
            screen="month",
            context={
                "action": "delete_living_expense",
                "living_expense_id": command.living_expense_id,
            },
        )
        self._logger.info(f"生活費削除: ID {command.living_expense_id}", context)

    async def get_living_expense_data(self, year: int, month: int) -> LivingExpenseData:
        """生活費データを取得（カテゴリ別一覧・合計）

        Args:
            year: 年
            month: 月

        Returns:
            生活費データ
        """
        ym = YearMonth(year, month)
        expenses = await self._living_expense_repo.find_by_year_month(ym)

        by_category: dict[str, list[LivingExpense]] = {cat: [] for cat in LIVING_EXPENSE_CATEGORIES}
        for e in expenses:
            if e.category in by_category:
                by_category[e.category].append(e)

        totals_by_category: dict[str, Money] = {}
        for cat in LIVING_EXPENSE_CATEGORIES:
            items = by_category.get(cat, [])
            total = Money(sum(i.amount.amount for i in items))
            totals_by_category[cat] = total

        return LivingExpenseData(
            by_category=by_category,
            totals_by_category=totals_by_category,
        )
