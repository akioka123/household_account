from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, order=True)
class YearMonth:
    year: int
    month: int

    def __post_init__(self) -> None:
        if self.year < 1900 or self.year > 9999:
            raise ValueError("year out of range")
        if self.month < 1 or self.month > 12:
            raise ValueError("month out of range")

    def next_month(self) -> "YearMonth":
        if self.month == 12:
            return YearMonth(self.year + 1, 1)
        return YearMonth(self.year, self.month + 1)
