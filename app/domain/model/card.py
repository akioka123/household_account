"""カードのエンティティ"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Card:
    """カードマスタ"""

    id: int
    """カードID"""
    name: str
    """カード名"""
    enabled: bool
    """有効フラグ"""

    def disable(self) -> Card:
        """カードを無効化（新しいインスタンスを返す）"""
        return Card(id=self.id, name=self.name, enabled=False)

    def enable(self) -> Card:
        """カードを有効化（新しいインスタンスを返す）"""
        return Card(id=self.id, name=self.name, enabled=True)

    def rename(self, new_name: str) -> Card:
        """カード名を変更（新しいインスタンスを返す）"""
        return Card(id=self.id, name=new_name, enabled=self.enabled)

