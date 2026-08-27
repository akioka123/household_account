"""カード請求の永続化Port"""
from __future__ import annotations

from typing import Protocol

from app.domain.model.card_statement import CardStatement
from app.domain.model.year_month import YearMonth


class CardStatementRepository(Protocol):
    """カード請求の永続化Port"""

    async def find_by_year_month(self, ym: YearMonth) -> list[CardStatement]:
        """指定年月のカード請求を取得"""
        ...

    async def find_all(self) -> list[CardStatement]:
        """全カード請求を取得"""
        ...

    async def save(self, statement: CardStatement) -> None:
        """カード請求を保存（新規作成または更新）"""
        ...

    async def delete(self, statement_id: int) -> None:
        """カード請求を削除"""
        ...

