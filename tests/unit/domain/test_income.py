"""Incomeのテスト"""
from __future__ import annotations

from app.domain.model.income import Income
from app.domain.model.money import Money


def test_income_creation() -> None:
    """Incomeの作成"""
    income = Income.of(
        salary_gross=500000,
        salary_net=400000,
        bonus_gross=1000000,
        bonus_net=800000,
    )
    assert income.salary_gross.amount == 500000
    assert income.salary_net.amount == 400000
    assert income.bonus_gross.amount == 1000000
    assert income.bonus_net.amount == 800000


def test_income_net_total() -> None:
    """手取り合計を計算"""
    income = Income.of(
        salary_gross=500000,
        salary_net=400000,
        bonus_gross=1000000,
        bonus_net=800000,
    )
    net_total = income.net_total()
    assert net_total.amount == 1200000
