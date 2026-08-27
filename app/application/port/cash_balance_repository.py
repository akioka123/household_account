"""月初現金の永続化Port"""
from __future__ import annotations

from typing import Protocol

from app.domain.model.cash_balance import CashBalance
from app.domain.model.year_month import YearMonth


class CashBalanceRepository(Protocol):
    """月初現金の永続化Port"""

    async def find(self, ym: YearMonth) -> CashBalance | None:
        """指定年月の月初現金を取得"""
        ...

    async def find_all(self) -> list[CashBalance]:
        """全月初現金を取得"""
        ...

    async def save(self, balance: CashBalance) -> None:
        """月初現金を保存（新規作成または更新）"""
        ...
