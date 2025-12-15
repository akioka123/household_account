"""月次集計ロジックのドメインサービス"""
from __future__ import annotations

from app.domain.model.money import Money
from app.domain.model.year_month import YearMonth


class MonthCalculator:
    """月次集計ロジックを提供するドメインサービス
    
    注意: このクラスは集計ロジックのみを提供し、
    データの取得はRepository層に委譲する。
    """

    @staticmethod
    def calculate_profit(
        net_income: Money,
        fixed_total: Money,
        variable_total: Money,
    ) -> Money:
        """損益を計算
        
        Args:
            net_income: 手取り収入合計
            fixed_total: 固定費合計
            variable_total: 変動費合計
        
        Returns:
            損益（手取り収入 - 固定費 - 変動費）
        """
        return net_income - fixed_total - variable_total

    @staticmethod
    def calculate_variable_total(
        variable_card: Money,
        cash_spent: Money,
    ) -> Money:
        """変動費合計を計算
        
        Args:
            variable_card: カード変動費
            cash_spent: 現金支出
        
        Returns:
            変動費合計
        """
        return variable_card + cash_spent

    @staticmethod
    def calculate_variable_card(
        card_statements_total: Money,
        fixed_in_card_total: Money,
    ) -> Money:
        """カード変動費を計算
        
        Args:
            card_statements_total: カード請求総額
            fixed_in_card_total: カードに含まれる固定費合計
        
        Returns:
            カード変動費（カード請求 - カード固定費）
        """
        return card_statements_total - fixed_in_card_total

    @staticmethod
    def calculate_cash_spent(
        cash_start: Money,
        withdrawals_total: Money,
        next_cash_start: Money,
    ) -> Money:
        """現金支出を計算
        
        Args:
            cash_start: 月初現金
            withdrawals_total: 引出総額
            next_cash_start: 次月月初現金
        
        Returns:
            現金支出（月初現金 + 引出 - 次月月初現金）
        """
        return cash_start + withdrawals_total - next_cash_start
