from __future__ import annotations

from app.application.port.income_repository import IncomeRepository
from app.domain.model.year_month import YearMonth
from app.domain.model.income import Income


class InMemoryIncomeRepository(IncomeRepository):
    """テスト/最小動作確認用のAdapter（infrastructure）。"""

    def __init__(self) -> None:
        self._store: dict[YearMonth, Income] = {}

    def upsert(self, ym: YearMonth, income: Income) -> None:
        self._store[ym] = income

    def find(self, ym: YearMonth) -> Income | None:
        return self._store.get(ym)
