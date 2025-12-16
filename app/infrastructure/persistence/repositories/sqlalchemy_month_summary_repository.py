"""月次サマリのSQLAlchemy実装"""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.port.cash_balance_repository import CashBalanceRepository
from app.application.port.card_statement_repository import CardStatementRepository
from app.application.port.fixed_item_history_repository import FixedItemHistoryRepository
from app.application.port.income_repository import IncomeRepository
from app.application.port.month_summary_repository import MonthSummaryRepository
from app.application.port.withdrawal_repository import WithdrawalRepository
from app.domain.model.money import Money
from app.domain.model.month_summary import MonthSummary
from app.domain.service.month_calculator import MonthCalculator
from app.domain.model.year_month import YearMonth
from app.infrastructure.persistence.repositories.sqlalchemy_cash_balance_repository import (
    SqlAlchemyCashBalanceRepository,
)
from app.infrastructure.persistence.repositories.sqlalchemy_card_statement_repository import (
    SqlAlchemyCardStatementRepository,
)
from app.infrastructure.persistence.repositories.sqlalchemy_fixed_item_history_repository import (
    SqlAlchemyFixedItemHistoryRepository,
)
from app.infrastructure.persistence.repositories.sqlalchemy_income_repository import (
    SqlAlchemyIncomeRepository,
)
from app.infrastructure.persistence.repositories.sqlalchemy_withdrawal_repository import (
    SqlAlchemyWithdrawalRepository,
)


class SqlAlchemyMonthSummaryRepository:
    """月次サマリのSQLAlchemy実装"""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        # 必要なRepositoryを初期化
        self._income_repo: IncomeRepository = SqlAlchemyIncomeRepository(session)
        self._fixed_item_history_repo: FixedItemHistoryRepository = (
            SqlAlchemyFixedItemHistoryRepository(session)
        )
        self._card_statement_repo: CardStatementRepository = (
            SqlAlchemyCardStatementRepository(session)
        )
        self._cash_balance_repo: CashBalanceRepository = SqlAlchemyCashBalanceRepository(session)
        self._withdrawal_repo: WithdrawalRepository = SqlAlchemyWithdrawalRepository(session)

    async def find_by_year(self, year: int) -> list[MonthSummary]:
        """指定年の全月のサマリを取得"""
        summaries: list[MonthSummary] = []
        for month in range(1, 13):
            ym = YearMonth(year, month)
            summary = await self._calculate_summary(ym)
            if summary:
                summaries.append(summary)
        return summaries

    async def find(self, ym: YearMonth) -> MonthSummary | None:
        """指定年月のサマリを取得"""
        return await self._calculate_summary(ym)

    async def _calculate_summary(self, ym: YearMonth) -> MonthSummary | None:
        """月次サマリを計算"""
        next_ym = YearMonth(ym.year, ym.month + 1) if ym.month < 12 else YearMonth(ym.year + 1, 1)

        # 収入を取得
        income = await self._income_repo.find(ym)
        net_income = Money(income.net_total().amount) if income else Money(0)

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
        variable_card_total_amount = 0
        for card_id, statement_total in card_statements_by_card.items():
            fixed_in_card = fixed_in_card_by_card.get(card_id, Money(0))
            variable_card_amount = MonthCalculator.calculate_variable_card_amount(
                statement_total, fixed_in_card
            )
            variable_card_total_amount += variable_card_amount
        variable_card_total = Money(max(0, variable_card_total_amount))

        # 現金支出を計算
        cash_start = await self._cash_balance_repo.find(ym)
        withdrawals = await self._withdrawal_repo.find_by_year_month(ym)
        next_cash_start = await self._cash_balance_repo.find(next_ym)

        cash_spent = Money(0)
        if cash_start:
            withdrawals_total = Money(sum(w.amount.amount for w in withdrawals))
            if next_cash_start:
                cash_spent_amount = MonthCalculator.calculate_cash_spent_amount(
                    cash_start, withdrawals_total, next_cash_start
                )
                cash_spent = Money(max(0, cash_spent_amount))
            else:
                # 次月月初現金が未登録の場合は、月初現金 + 引出を表示用として使用
                cash_spent = cash_start.amount + withdrawals_total

        # 変動費合計を計算
        variable_total = MonthCalculator.calculate_variable_total(
            variable_card_total, cash_spent
        )

        # 損益を計算
        profit_amount = MonthCalculator.calculate_profit_amount(net_income, fixed_total, variable_total)

        # 月次サマリを作成
        summary = MonthSummary.calculate(ym, net_income, fixed_total, variable_total, profit_amount)

        return summary


# Protocol実装として登録
MonthSummaryRepository.register(SqlAlchemyMonthSummaryRepository)

