"""金額のValue Object"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Money:
    """金額（円）。コンストラクタは検証しない（損益など負の値を直接表現するため）。

    `__sub__` は結果が負になる場合のみ例外を送出する。0以上を保証したい箇所（フォーム入力等）は
    呼び出し側で検証すること。
    """

    amount: int

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

