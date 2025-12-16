"""金額のValue Object"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Money:
    """金額（円）。不変条件：0以上。"""

    amount: int

    def __post_init__(self) -> None:
        """不変条件の検証"""
        if self.amount < 0:
            raise ValueError("Money must be >= 0")

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

    @classmethod
    def from_amount_unsafe(cls, amount: int) -> Money:
        """負の値を許容するMoneyオブジェクトを作成（内部計算用）
        
        注意: このメソッドは中間計算で負の値が必要な場合にのみ使用する。
        最終的な金額は通常のコンストラクタで検証される。
        
        Args:
            amount: 金額（負の値も許容）
        
        Returns:
            Moneyオブジェクト
        """
        # バリデーションをスキップして直接インスタンスを作成
        instance = object.__new__(cls)
        instance.amount = amount
        return instance
