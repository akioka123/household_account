from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Money:
    """金額（円）。不変条件：0以上。"""
    amount: int

    def __post_init__(self) -> None:
        if self.amount < 0:
            raise ValueError("Money must be >= 0")

    def __add__(self, other: "Money") -> "Money":
        return Money(self.amount + other.amount)

    def __sub__(self, other: "Money") -> "Money":
        v = self.amount - other.amount
        if v < 0:
            raise ValueError("Money subtraction would be negative")
        return Money(v)
