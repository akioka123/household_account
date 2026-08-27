"""生活費品目（レシート内の1行）のエンティティ"""
from __future__ import annotations

from dataclasses import dataclass

from app.domain.model.money import Money

# 品目の小分類（内部値）
LIVING_EXPENSE_ITEM_SUBCATEGORY_GROCERY = "grocery"
LIVING_EXPENSE_ITEM_SUBCATEGORY_DAILY_GOODS = "daily_goods"

LIVING_EXPENSE_ITEM_SUBCATEGORIES = [
    LIVING_EXPENSE_ITEM_SUBCATEGORY_GROCERY,
    LIVING_EXPENSE_ITEM_SUBCATEGORY_DAILY_GOODS,
]

# 小分類の内部値 → 画面表示ラベルの対応（貼り付けテキストの解析にも用いる）
LIVING_EXPENSE_ITEM_SUBCATEGORY_LABELS: dict[str, str] = {
    LIVING_EXPENSE_ITEM_SUBCATEGORY_GROCERY: "食品",
    LIVING_EXPENSE_ITEM_SUBCATEGORY_DAILY_GOODS: "生活用品",
}


@dataclass(frozen=True)
class LivingExpenseItem:
    """生活費品目（レシート1件に紐づく品目の1行）"""

    id: int
    """品目ID"""
    living_expense_id: int
    """親レシート（LivingExpense）のID"""
    name: str
    """品目名"""
    amount: Money
    """金額"""
    sub_category: str
    """小分類（grocery / daily_goods）"""

    def __post_init__(self) -> None:
        """不変条件の検証"""
        if not self.name or not self.name.strip():
            raise ValueError("品目名を入力してください")
        if self.amount.amount < 0:
            raise ValueError("金額は0以上の整数で入力してください")
        if self.sub_category not in LIVING_EXPENSE_ITEM_SUBCATEGORIES:
            raise ValueError("小分類は食品または生活用品のいずれかを指定してください")
