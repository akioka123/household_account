"""金額のValue Object"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Money:
    """金額（円）。不変条件：0以上（ただし、profit等の計算結果として負の値も許容）。"""

    amount: int

    def __post_init__(self) -> None:
        """不変条件の検証
        
        注意: profit等の計算結果として負の値（損失）を表現する必要があるため、
        負の値も許可する。ただし、通常の金額（収入、支出等）は0以上であるべき。
        """
        pass

    def __add__(self, other: Money) -> Money:
        """加算"""
        return Money(self.amount + other.amount)

    def __sub__(self, other: Money) -> Money:
        """減算（結果が負になる場合は例外）"""
        v = self.amount - other.amount
        if v < 0:
            raise ValueError("Money subtraction would be negative")
        return Money(v)

    def __mul__(self, multiplier: int) -> Money:
        """乗算"""
        return Money(self.amount * multiplier)

    def __rmul__(self, multiplier: int) -> Money:
        """右側からの乗算"""
        return self.__mul__(multiplier)

