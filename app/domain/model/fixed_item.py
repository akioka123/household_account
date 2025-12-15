"""固定費項目のエンティティ"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FixedItem:
    """固定費項目（マスタ）"""

    id: int
    """固定費項目ID"""
    name: str
    """項目名"""

    def rename(self, new_name: str) -> FixedItem:
        """項目名を変更（新しいインスタンスを返す）"""
        return FixedItem(id=self.id, name=new_name)
