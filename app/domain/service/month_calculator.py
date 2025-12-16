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
            注意: 支出が収入を上回る場合、負の値（赤字）になる可能性がある
        """
        # 負の値を許容する中間計算として、整数計算を行い結果を返す
        result_amount = net_income.amount - fixed_total.amount - variable_total.amount
        return Money.from_amount_unsafe(result_amount)

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
            注意: 固定費がカード請求を上回る場合、負の値になる可能性がある
        """
        # 負の値を許容する中間計算として、整数計算を行い結果を返す
        result_amount = card_statements_total.amount - fixed_in_card_total.amount
        return Money.from_amount_unsafe(result_amount)

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
            注意: 次月月初現金が月初現金+引出を上回る場合、負の値になる可能性がある
        """
        # 負の値を許容する中間計算として、整数計算を行い結果を返す
        result_amount = cash_start.amount + withdrawals_total.amount - next_cash_start.amount
        return Money.from_amount_unsafe(result_amount)
