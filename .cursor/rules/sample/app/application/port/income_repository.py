from __future__ import annotations

from typing import Protocol

from app.domain.model.year_month import YearMonth
from app.domain.model.income import Income


class IncomeRepository(Protocol):
    """収入の永続化Port。UseCaseはこのProtocolのみに依存する。"""

    def upsert(self, ym: YearMonth, income: Income) -> None: ...
    def find(self, ym: YearMonth) -> Income | None: ...
