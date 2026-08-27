"""Moneyのテスト"""
from __future__ import annotations

import pytest

from app.domain.model.money import Money


def test_money_creation() -> None:
    """Moneyの作成"""
    money = Money(1000)
    assert money.amount == 1000


def test_money_negative_amount() -> None:
    """負の金額も許可（損益計算などで必要）"""
    money = Money(-1000)
    assert money.amount == -1000


def test_money_addition() -> None:
    """Moneyの加算"""
    m1 = Money(1000)
    m2 = Money(500)
    result = m1 + m2
    assert result.amount == 1500


def test_money_subtraction() -> None:
    """Moneyの減算"""
    m1 = Money(1000)
    m2 = Money(300)
    result = m1 - m2
    assert result.amount == 700


def test_money_subtraction_negative_result() -> None:
    """減算結果が負になる場合、例外を発生"""
    m1 = Money(1000)
    m2 = Money(1500)
    with pytest.raises(ValueError, match="Money subtraction would be negative"):
        _ = m1 - m2
