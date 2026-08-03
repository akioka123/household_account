"""月次メモの永続化Port"""

from __future__ import annotations

from typing import Protocol

from app.domain.model.month_note import MonthNote
from app.domain.model.year_month import YearMonth


class MonthNoteRepository(Protocol):
    """月次メモの永続化Port"""

    async def find(self, ym: YearMonth) -> MonthNote | None:
        """指定年月の月次メモを取得"""
        ...

    async def find_by_year(self, year: int) -> dict[YearMonth, MonthNote]:
        """指定年の月次メモを年月をキーにして取得"""
        ...

    async def save(self, note: MonthNote) -> None:
        """月次メモを保存（新規作成または更新）"""
        ...

    async def delete(self, ym: YearMonth) -> None:
        """指定年月の月次メモを削除"""
        ...
