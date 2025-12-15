"""収入の永続化Port"""
from __future__ import annotations

from typing import Protocol

from app.domain.model.income import Income
from app.domain.model.year_month import YearMonth


class IncomeRepository(Protocol):
    """収入の永続化Port。UseCaseはこのProtocolのみに依存する"""

    async def upsert(self, ym: YearMonth, income: Income) -> None:
        """収入を登録または更新"""
        ...

    async def find(self, ym: YearMonth) -> Income | None:
        """指定年月の収入を取得"""
        ...

    async def find_by_year(self, year: int) -> dict[YearMonth, Income]:
        """指定年の全月の収入を取得"""
        ...
