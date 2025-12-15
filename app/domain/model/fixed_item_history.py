"""固定費履歴のエンティティ"""
from __future__ import annotations

from dataclasses import dataclass

from app.domain.model.money import Money
from app.domain.model.year_month import YearMonth


@dataclass(frozen=True)
class FixedItemHistory:
    """固定費履歴（適用開始年月、金額、カード紐づけ、カード含有フラグ）"""

    id: int
    """履歴ID"""
    fixed_item_id: int
    """固定費項目ID"""
    effective_from: YearMonth
    """適用開始年月"""
    amount: Money
    """金額（0の場合は削除を意味する）"""
    card_id: int | None
    """カード紐づけ（任意）"""
    included_in_card: bool
    """カード請求に含まれる固定費かどうか"""

    def is_active_at(self, ym: YearMonth) -> bool:
        """指定年月で有効かどうかを判定"""
        return self.effective_from <= ym

    def is_deleted(self) -> bool:
        """削除済みかどうかを判定（金額0の場合）"""
        return self.amount.amount == 0
