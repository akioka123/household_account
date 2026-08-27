"""月初現金のエンティティ"""
from __future__ import annotations

from dataclasses import dataclass

from app.domain.model.money import Money
from app.domain.model.year_month import YearMonth


@dataclass(frozen=True)
class CashBalance:
    """月初現金（年月：月初現金）"""

    id: int
    """月初現金ID"""
    year_month: YearMonth
    """対象年月"""
    amount: Money
    """月初現金"""
