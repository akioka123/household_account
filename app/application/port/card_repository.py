"""カードの永続化Port"""
from __future__ import annotations

from typing import Protocol

from app.domain.model.card import Card


class CardRepository(Protocol):
    """カードの永続化Port"""

    async def find_all(self) -> list[Card]:
        """全カードを取得"""
        ...

    async def find_by_id(self, card_id: int) -> Card | None:
        """IDでカードを取得"""
        ...

    async def save(self, card: Card) -> None:
        """カードを保存（新規作成または更新）"""
        ...

    async def delete(self, card_id: int) -> None:
        """カードを削除"""
        ...

