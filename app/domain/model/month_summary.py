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
        profit_amount: int,
    ) -> MonthSummary:
        """月次サマリを計算して作成
        
        Args:
            year_month: 対象年月
            net_income: 手取り収入合計
            fixed_total: 固定費合計
            variable_total: 変動費合計
            profit_amount: 損益の整数値（負の値も許容）
        
        Returns:
            月次サマリ
        """
        # 損益が負の場合は0として扱う（表示用）
        profit = Money(max(0, profit_amount))
        return MonthSummary(
            year_month=year_month,
            net_income=net_income,
            fixed_total=fixed_total,
            variable_total=variable_total,
            profit=profit,
        )
