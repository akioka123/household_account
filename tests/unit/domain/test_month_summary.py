"""MonthSummaryのテスト"""
from __future__ import annotations

from app.domain.model.month_summary import MonthSummary
from app.domain.model.money import Money
from app.domain.model.year_month import YearMonth


def test_month_summary_calculate() -> None:
    """MonthSummaryの計算"""
    ym = YearMonth(2024, 5)
    net_income = Money(500000)
    fixed_total = Money(100000)
    variable_total = Money(200000)
    profit_amount = 200000  # 500000 - 100000 - 200000

    summary = MonthSummary.calculate(ym, net_income, fixed_total, variable_total, profit_amount)

    assert summary.year_month == ym
    assert summary.net_income == net_income
    assert summary.fixed_total == fixed_total
    assert summary.variable_total == variable_total
    assert summary.profit.amount == profit_amount


def test_month_summary_calculate_negative_profit() -> None:
    """損益が負の値（赤字）の場合も正しく計算"""
    ym = YearMonth(2024, 5)
    net_income = Money(300000)
    fixed_total = Money(100000)
    variable_total = Money(250000)
    profit_amount = -50000  # 300000 - 100000 - 250000

    summary = MonthSummary.calculate(ym, net_income, fixed_total, variable_total, profit_amount)

    assert summary.profit.amount == -50000
    assert summary.profit.amount < 0
