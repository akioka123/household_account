"""年月のValue Object"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, order=True)
class YearMonth:
    """年月を表すValue Object（YYYY-MM形式、不変）"""

    year: int
    month: int

    def __post_init__(self) -> None:
        """不変条件の検証"""
        if self.year < 1900 or self.year > 9999:
            raise ValueError("year out of range")
        if self.month < 1 or self.month > 12:
            raise ValueError("month out of range")

    def next_month(self) -> YearMonth:
        """次の月を取得"""
        if self.month == 12:
            return YearMonth(self.year + 1, 1)
        return YearMonth(self.year, self.month + 1)

    def to_string(self) -> str:
        """YYYY-MM形式の文字列に変換"""
        return f"{self.year}-{self.month:02d}"

    @staticmethod
    def from_string(ym_str: str) -> YearMonth:
        """YYYY-MM形式の文字列からYearMonthを作成"""
        parts = ym_str.split("-")
        if len(parts) != 2:
            raise ValueError(f"Invalid YearMonth format: {ym_str}")
        return YearMonth(int(parts[0]), int(parts[1]))
