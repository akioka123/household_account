"""Withdrawalのテスト"""
from __future__ import annotations

from datetime import date

from app.domain.model.money import Money
from app.domain.model.withdrawal import Withdrawal
from app.domain.model.year_month import YearMonth


def test_withdrawal_creation() -> None:
    """Withdrawalの作成"""
    ym = YearMonth(2024, 3)
    withdrawal = Withdrawal(
        id=1,
        year_month=ym,
        withdrawal_date=date(2024, 3, 15),
        amount=Money(50000),
        note="食費",
    )
    assert withdrawal.id == 1
    assert withdrawal.year_month == ym
    assert withdrawal.withdrawal_date == date(2024, 3, 15)
    assert withdrawal.amount.amount == 50000
    assert withdrawal.note == "食費"


def test_withdrawal_without_note() -> None:
    """メモなしのWithdrawal"""
    ym = YearMonth(2024, 3)
    withdrawal = Withdrawal(
        id=1,
        year_month=ym,
        withdrawal_date=date(2024, 3, 15),
        amount=Money(50000),
        note="",
    )
    assert withdrawal.note == ""
