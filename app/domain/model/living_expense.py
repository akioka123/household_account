"""生活費のエンティティ"""
from __future__ import annotations

from dataclasses import dataclass

from app.domain.model.money import Money
from app.domain.model.year_month import YearMonth

# 生活費カテゴリ（内部値）
LIVING_EXPENSE_CATEGORY_FOOD = "food"
LIVING_EXPENSE_CATEGORY_ELECTRICITY = "electricity"
LIVING_EXPENSE_CATEGORY_GAS = "gas"
LIVING_EXPENSE_CATEGORY_MOBILE = "mobile"
LIVING_EXPENSE_CATEGORY_COMMUNICATION = "communication"

LIVING_EXPENSE_CATEGORIES = [
    LIVING_EXPENSE_CATEGORY_FOOD,
    LIVING_EXPENSE_CATEGORY_ELECTRICITY,
    LIVING_EXPENSE_CATEGORY_GAS,
    LIVING_EXPENSE_CATEGORY_MOBILE,
    LIVING_EXPENSE_CATEGORY_COMMUNICATION,
]


@dataclass(frozen=True)
class LivingExpense:
    """生活費（年月：生活費明細）"""

    id: int
    """生活費ID"""
    year_month: YearMonth
    """対象年月"""
    category: str
    """カテゴリ（food / electricity / gas / mobile / communication）"""
    location: str
    """場所（最大20文字、食費以外は空可）"""
    amount: Money
    """金額"""
    note: str
    """メモ（最大50文字、任意）"""
