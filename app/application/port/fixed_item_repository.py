"""固定費項目の永続化Port"""
from __future__ import annotations

from typing import Protocol

from app.domain.model.fixed_item import FixedItem


class FixedItemRepository(Protocol):
    """固定費項目の永続化Port"""

    async def find_all(self) -> list[FixedItem]:
        """全固定費項目を取得"""
        ...

    async def find_by_id(self, fixed_item_id: int) -> FixedItem | None:
        """IDで固定費項目を取得"""
        ...

    async def save(self, fixed_item: FixedItem) -> None:
        """固定費項目を保存（新規作成または更新）"""
        ...
