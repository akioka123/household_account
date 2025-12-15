"""月次サマリのエンティティ"""
from __future__ import annotations

from dataclasses import dataclass

from app.domain.model.money import Money
from app.domain.model.year_month import YearMonth


@dataclass(frozen=True)
class MonthSummary:
    """月次サマリ（年月、手取り収入、固定費、変動費、損益）"""

    year_month: YearMonth
    """対象年月"""
    net_income: Money
    """手取り収入合計（salary_net + bonus_net）"""
    fixed_total: Money
    """固定費合計"""
    variable_total: Money
    """変動費合計"""
    profit: Money
    """損益（手取り収入 - 固定費 - 変動費）"""

    @staticmethod
    def calculate(
        year_month: YearMonth,
        net_income: Money,
        fixed_total: Money,
        variable_total: Money,
    ) -> MonthSummary:
        """月次サマリを計算して作成"""
        profit = net_income - fixed_total - variable_total
        return MonthSummary(
            year_month=year_month,
            net_income=net_income,
            fixed_total=fixed_total,
            variable_total=variable_total,
            profit=profit,
        )
