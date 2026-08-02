"""ダッシュボードデータ取得ユースケース"""
from __future__ import annotations

from dataclasses import dataclass

from app.application.port.income_repository import IncomeRepository
from app.application.port.living_expense_repository import LivingExpenseRepository
from app.application.port.logger import Logger
from app.application.port.month_summary_repository import MonthSummaryRepository
from app.domain.model.living_expense import LIVING_EXPENSE_CATEGORIES
from app.domain.model.money import Money
from app.domain.model.month_summary import MonthSummary
from app.domain.model.year_month import YearMonth


@dataclass(frozen=True)
class DashboardData:
    """ダッシュボード表示用データ"""

    year: int
    """対象年"""
    month_summaries: list[MonthSummary]
    """月別サマリ一覧（12ヶ月分）"""
    annual_gross: int
    """年収（額面）"""
    annual_net: int
    """年収（手取り）"""
    living_expenses_by_month: dict[YearMonth, dict[str, Money]]
    """月別・カテゴリ別生活費合計（食費・電気代・ガス代・携帯料金・通信費）"""


class GetDashboardDataUseCase:
    """ダッシュボードデータ取得ユースケース"""

    def __init__(
        self,
        month_summary_repo: MonthSummaryRepository,
        income_repo: IncomeRepository,
        living_expense_repo: LivingExpenseRepository,
        logger: Logger,
    ) -> None:
        self._month_summary_repo = month_summary_repo
        self._income_repo = income_repo
        self._living_expense_repo = living_expense_repo
        self._logger = logger

    async def execute(self, year: int) -> DashboardData:
        """ダッシュボードデータを取得

        Args:
            year: 対象年

        Returns:
            ダッシュボード表示用データ
        """
        from app.domain.model.log_context import LogContext

        context = LogContext(screen="dashboard", context={"year": year})
        self._logger.info(f"ダッシュボードデータ取得開始: {year}年", context)

        month_summaries = await self._month_summary_repo.find_by_year(year)
        annual_gross, annual_net = await self._calculate_annual_income(year)
        living_expenses_by_month = await self._calculate_living_expenses_by_month(year)

        self._logger.info(f"ダッシュボードデータ取得完了: {year}年", context)

        return DashboardData(
            year=year,
            month_summaries=month_summaries,
            annual_gross=annual_gross,
            annual_net=annual_net,
            living_expenses_by_month=living_expenses_by_month,
        )

    async def _calculate_annual_income(self, year: int) -> tuple[int, int]:
        """年収（額面・手取り）を計算"""
        incomes = await self._income_repo.find_by_year(year)

        annual_gross = 0
        annual_net = 0

        for income in incomes.values():
            annual_gross += income.gross_total().amount
            annual_net += income.net_total().amount

        return annual_gross, annual_net

    async def _calculate_living_expenses_by_month(
        self, year: int
    ) -> dict[YearMonth, dict[str, Money]]:
        """各月の生活費をカテゴリ別に計算"""
        result: dict[YearMonth, dict[str, Money]] = {}

        for month in range(1, 13):
            ym = YearMonth(year, month)
            expenses = await self._living_expense_repo.find_by_year_month(ym)
            by_cat: dict[str, Money] = {}
            for cat in LIVING_EXPENSE_CATEGORIES:
                total = sum(e.amount.amount for e in expenses if e.category == cat)
                by_cat[cat] = Money(total)
            result[ym] = by_cat

        return result
