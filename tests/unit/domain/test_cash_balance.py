"""CashBalanceのテスト"""
from __future__ import annotations

from app.domain.model.cash_balance import CashBalance
from app.domain.model.money import Money
from app.domain.model.year_month import YearMonth


def test_cash_balance_creation() -> None:
    """CashBalanceの作成"""
    ym = YearMonth(2024, 3)
    balance = CashBalance(
        id=1,
        year_month=ym,
        amount=Money(100000),
    )
    assert balance.id == 1
    assert balance.year_month == ym
    assert balance.amount.amount == 100000
