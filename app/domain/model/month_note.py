"""月次メモのエンティティ"""
from __future__ import annotations

from dataclasses import dataclass

from app.domain.model.year_month import YearMonth

MONTH_NOTE_MAX_LENGTH = 500
"""月次メモの最大文字数"""


@dataclass(frozen=True)
class MonthNote:
    """月次メモ（当月の消費が平均以上／以下になった理由）"""

    id: int
    """月次メモID（未採番の場合は0）"""
    year_month: YearMonth
    """対象年月"""
    note: str
    """メモ本文（最大500文字）"""

    def __post_init__(self) -> None:
        """不変条件の検証"""
        if len(self.note) > MONTH_NOTE_MAX_LENGTH:
            raise ValueError(f"メモは{MONTH_NOTE_MAX_LENGTH}文字以内で入力してください。")

    @staticmethod
    def of(year_month: YearMonth, note: str) -> MonthNote:
        """未採番の月次メモを作成

        Args:
            year_month: 対象年月
            note: メモ本文（前後の空白は除去する）

        Returns:
            月次メモ
        """
        return MonthNote(id=0, year_month=year_month, note=note.strip())

    def is_empty(self) -> bool:
        """メモが空かどうか"""
        return self.note == ""
