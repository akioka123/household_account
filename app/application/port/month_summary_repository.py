"""月次サマリの永続化Port"""
from __future__ import annotations

from typing import Protocol

from app.domain.model.month_summary import MonthSummary
from app.domain.model.year_month import YearMonth


class MonthSummaryRepository(Protocol):
    """月次サマリの永続化Port（集計結果取得用）"""

    async def find_by_year(self, year: int) -> list[MonthSummary]:
        """指定年の全月のサマリを取得"""
        ...

    async def find(self, ym: YearMonth) -> MonthSummary | None:
        """指定年月のサマリを取得"""
        ...

