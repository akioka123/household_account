"""固定費履歴の永続化Port"""
from __future__ import annotations

from typing import Protocol

from app.domain.model.fixed_item_history import FixedItemHistory
from app.domain.model.year_month import YearMonth


class FixedItemHistoryRepository(Protocol):
    """固定費履歴の永続化Port"""

    async def find_by_fixed_item_id(self, fixed_item_id: int) -> list[FixedItemHistory]:
        """固定費項目IDで履歴を取得（適用開始年月順）"""
        ...

    async def find_active_at(self, ym: YearMonth) -> list[FixedItemHistory]:
        """指定年月で有効な履歴を取得"""
        ...

    async def save(self, history: FixedItemHistory) -> None:
        """固定費履歴を保存（新規作成）"""
        ...
