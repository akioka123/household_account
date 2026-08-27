"""カード請求のエンティティ"""
from __future__ import annotations

from dataclasses import dataclass

from app.domain.model.money import Money
from app.domain.model.year_month import YearMonth


@dataclass(frozen=True)
class CardStatement:
    """カード請求（年月×カード：請求総額）"""

    id: int
    """カード請求ID"""
    year_month: YearMonth
    """対象年月"""
    card_id: int
    """カードID"""
    amount: Money
    """請求総額"""

