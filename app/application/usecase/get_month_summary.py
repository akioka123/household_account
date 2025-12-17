"""月次サマリ取得ユースケース"""
from __future__ import annotations

from dataclasses import dataclass

from app.application.port.cash_balance_repository import CashBalanceRepository
from app.application.port.card_repository import CardRepository
from app.application.port.card_statement_repository import CardStatementRepository
from app.application.port.fixed_item_history_repository import FixedItemHistoryRepository
from app.application.port.income_repository import IncomeRepository
from app.application.port.logger import Logger
from app.application.port.withdrawal_repository import WithdrawalRepository
from app.domain.model.income import Income
from app.domain.model.money import Money
from app.domain.model.month_summary import MonthSummary
from app.domain.model.fixed_expenses import FixedExpenses
from app.domain.service.month_calculator import MonthCalculator
from app.domain.model.year_month import YearMonth


@dataclass(frozen=True)
class MonthSummaryResult:
    """月次サマリ結果（警告情報を含む）"""

    summary: MonthSummary
    """月次サマリ"""
    warnings: list[str]
    """警告メッセージのリスト"""
    cash_spent_uncertain: bool
    """現金支出が未確定かどうか（次月月初現金未登録）"""
    variable_card_negative: bool
    """カード変動費が負値かどうか"""


class GetMonthSummaryUseCase:
    """月次サマリ取得ユースケース"""

    def __init__(
        self,
        income_repo: IncomeRepository,
        fixed_item_history_repo: FixedItemHistoryRepository,
        card_statement_repo: CardStatementRepository,
        cash_balance_repo: CashBalanceRepository,
        withdrawal_repo: WithdrawalRepository,
        card_repo: CardRepository,
        logger: Logger,
    ) -> None:
        self._income_repo = income_repo
        self._fixed_item_history_repo = fixed_item_history_repo
        self._card_statement_repo = card_statement_repo
        self._cash_balance_repo = cash_balance_repo
        self._withdrawal_repo = withdrawal_repo
        self._card_repo = card_repo
        self._logger = logger

    async def execute(self, year: int, month: int) -> MonthSummaryResult:
        """月次サマリを取得

        Args:
            year: 年
            month: 月

        Returns:
            月次サマリ結果
        """
        ym = YearMonth(year, month)
        next_ym = ym.next_month()

        # 収入を取得
        income = await self._income_repo.find(ym)
        net_income = (
            Money(income.net_total().amount) if income else Money(0)
        )

        # 固定費を取得
        fixed_histories = await self._fixed_item_history_repo.find_active_at(ym)
        fixed_expenses = FixedExpenses.calculate(fixed_histories)
        fixed_total = fixed_expenses.total
        fixed_in_card_by_card = fixed_expenses.by_card

        # カード請求を取得
        card_statements = await self._card_statement_repo.find_by_year_month(ym)
        card_statements_total = Money(0)
        card_statements_by_card: dict[int, Money] = {}  # カードIDごとの請求総額

        for statement in card_statements:
            card_statements_total = card_statements_total + statement.amount
            if statement.card_id not in card_statements_by_card:
                card_statements_by_card[statement.card_id] = Money(0)
            card_statements_by_card[statement.card_id] = (
                card_statements_by_card[statement.card_id] + statement.amount
            )

        # カード変動費を計算（カードごと）
        variable_card_total_amount = 0
        variable_card_negative = False
        for card_id, statement_total in card_statements_by_card.items():
            fixed_in_card = fixed_in_card_by_card.get(card_id, Money(0))
            variable_card_amount = MonthCalculator.calculate_variable_card_amount(
                statement_total, fixed_in_card
            )
            variable_card_total_amount += variable_card_amount
            if variable_card_amount < 0:
                variable_card_negative = True
        variable_card_total = Money(max(0, variable_card_total_amount))

        # 現金支出を計算
        cash_start = await self._cash_balance_repo.find(ym)
        withdrawals = await self._withdrawal_repo.find_by_year_month(ym)
        next_cash_start = await self._cash_balance_repo.find(next_ym)

        cash_spent_uncertain = False
        cash_spent = Money(0)

        if cash_start:
            withdrawals_total = Money(sum(w.amount.amount for w in withdrawals))
            if next_cash_start:
                cash_spent_amount = MonthCalculator.calculate_cash_spent_amount(
                    cash_start.amount, withdrawals_total, next_cash_start.amount
                )
                cash_spent = Money(max(0, cash_spent_amount))
            else:
                cash_spent_uncertain = True
                # 次月月初現金が未登録の場合は、現金支出を未確定扱い
                # 計算値は表示用（月初現金 + 引出）
                cash_spent = cash_start.amount + withdrawals_total

        # 変動費合計を計算
        variable_total = MonthCalculator.calculate_variable_total(
            variable_card_total, cash_spent
        )

        # 損益を計算（負の値も保持する）
        profit_amount = MonthCalculator.calculate_profit_amount(net_income, fixed_total, variable_total)

        # 月次サマリを作成
        summary = MonthSummary.calculate(ym, net_income, fixed_total, variable_total, profit_amount)

        # 警告メッセージを生成
        warnings: list[str] = []
        if cash_spent_uncertain:
            warnings.append("次月月初現金が未登録のため、現金支出が未確定です。")
        if variable_card_negative:
            warnings.append("カード変動費が負値になっています。固定費の設定を確認してください。")

        return MonthSummaryResult(
            summary=summary,
            warnings=warnings,
            cash_spent_uncertain=cash_spent_uncertain,
            variable_card_negative=variable_card_negative,
        )
