"""月次サマリのSQLAlchemy実装"""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.port.cash_balance_repository import CashBalanceRepository
from app.application.port.card_repository import CardRepository
from app.application.port.card_statement_repository import CardStatementRepository
from app.application.port.fixed_item_history_repository import FixedItemHistoryRepository
from app.application.port.income_repository import IncomeRepository
from app.application.port.withdrawal_repository import WithdrawalRepository
from app.application.usecase.get_month_summary import GetMonthSummaryUseCase
from app.domain.model.month_summary import MonthSummary
from app.domain.model.year_month import YearMonth
from app.infrastructure.logging.structured_logger import StructuredLogger
from app.infrastructure.persistence.repositories.sqlalchemy_card_repository import (
    SqlAlchemyCardRepository,
)
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
    """月次サマリのSQLAlchemy実装（集計はGetMonthSummaryUseCaseに委譲）"""

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
        self._card_repo: CardRepository = SqlAlchemyCardRepository(session)

    async def find_by_year(self, year: int) -> list[MonthSummary]:
        """指定年の全月のサマリを取得"""
        summaries: list[MonthSummary] = []
        for month in range(1, 13):
            ym = YearMonth(year, month)
            summary = await self._calculate_summary(ym)
            if summary:
                summaries.append(summary)
        return summaries

    async def find_by_years(self, start_year: int, end_year: int) -> list[MonthSummary]:
        """指定期間の全月のサマリを取得"""
        summaries: list[MonthSummary] = []
        for year in range(start_year, end_year + 1):
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
        """月次サマリを計算（GetMonthSummaryUseCaseの集計結果をそのまま使う）"""
        usecase = GetMonthSummaryUseCase(
            income_repo=self._income_repo,
            fixed_item_history_repo=self._fixed_item_history_repo,
            card_statement_repo=self._card_statement_repo,
            cash_balance_repo=self._cash_balance_repo,
            withdrawal_repo=self._withdrawal_repo,
            card_repo=self._card_repo,
            logger=StructuredLogger("month_summary_repository"),
        )
        result = await usecase.execute(ym.year, ym.month)
        return result.summary

