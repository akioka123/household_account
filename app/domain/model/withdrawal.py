"""引出明細のエンティティ"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from app.domain.model.money import Money
from app.domain.model.year_month import YearMonth


@dataclass(frozen=True)
class Withdrawal:
    """引出明細（年月：引出明細）"""

    id: int
    """引出明細ID"""
    year_month: YearMonth
    """対象年月"""
    withdrawal_date: date
    """引出日付"""
    amount: Money
    """引出金額"""
    note: str
    """メモ（任意）"""
