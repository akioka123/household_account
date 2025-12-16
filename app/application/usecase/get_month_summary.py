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
        next_ym = YearMonth(year, month + 1) if month < 12 else YearMonth(year + 1, 1)

        # 収入を取得
        income = await self._income_repo.find(ym)
        net_income = (
            Money(income.net_total().amount) if income else Money(0)
        )

        # 固定費を取得
        fixed_histories = await self._fixed_item_history_repo.find_active_at(ym)
        fixed_total = Money(0)
        fixed_in_card_by_card: dict[int, Money] = {}  # カードIDごとの固定費合計

        for history in fixed_histories:
            if history.is_deleted():
                continue
            fixed_total = fixed_total + history.amount
            if history.included_in_card and history.card_id:
                card_id = history.card_id
                if card_id not in fixed_in_card_by_card:
                    fixed_in_card_by_card[card_id] = Money(0)
                fixed_in_card_by_card[card_id] = (
                    fixed_in_card_by_card[card_id] + history.amount
                )

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
        variable_card_total = Money(0)
        variable_card_negative = False
        for card_id, statement_total in card_statements_by_card.items():
            fixed_in_card = fixed_in_card_by_card.get(card_id, Money(0))
            variable_card = MonthCalculator.calculate_variable_card(
                statement_total, fixed_in_card
            )
            variable_card_total = variable_card_total + variable_card
            if variable_card.amount < 0:
                variable_card_negative = True

        # 現金支出を計算
        cash_start = await self._cash_balance_repo.find(ym)
        withdrawals = await self._withdrawal_repo.find_by_year_month(ym)
        next_cash_start = await self._cash_balance_repo.find(next_ym)

        cash_spent_uncertain = False
        cash_spent = Money(0)

        if cash_start:
            withdrawals_total = Money(sum(w.amount.amount for w in withdrawals))
            if next_cash_start:
                cash_spent = MonthCalculator.calculate_cash_spent(
                    cash_start.amount, withdrawals_total, next_cash_start.amount
                )
            else:
                cash_spent_uncertain = True
                # 次月月初現金が未登録の場合は、現金支出を未確定扱い
                # 計算値は表示用（月初現金 + 引出）
                cash_spent = cash_start.amount + withdrawals_total

        # 変動費合計を計算
        variable_total = MonthCalculator.calculate_variable_total(
            variable_card_total, cash_spent
        )

        # 損益を計算
        profit = MonthCalculator.calculate_profit(net_income, fixed_total, variable_total)

        # 月次サマリを作成
        summary = MonthSummary.calculate(ym, net_income, fixed_total, variable_total)

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
