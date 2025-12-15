"""ダッシュボードデータ取得ユースケース"""
from __future__ import annotations

from dataclasses import dataclass

from app.application.port.income_repository import IncomeRepository
from app.application.port.logger import Logger
from app.application.port.month_summary_repository import MonthSummaryRepository
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


class GetDashboardDataUseCase:
    """ダッシュボードデータ取得ユースケース"""

    def __init__(
        self,
        month_summary_repo: MonthSummaryRepository,
        income_repo: IncomeRepository,
        logger: Logger,
    ) -> None:
        self._month_summary_repo = month_summary_repo
        self._income_repo = income_repo
        self._logger = logger

    async def execute(self, year: int) -> DashboardData:
        """ダッシュボードデータを取得
        
        Args:
            year: 対象年
        
        Returns:
            ダッシュボード表示用データ
        """
        # ログ出力
        from app.domain.model.log_context import LogContext

        context = LogContext(screen="dashboard", context={"year": year})
        self._logger.info(f"ダッシュボードデータ取得開始: {year}年", context)

        # 月別サマリを取得
        month_summaries = await self._month_summary_repo.find_by_year(year)

        # 年収を計算
        annual_gross, annual_net = await self._calculate_annual_income(year)

        self._logger.info(f"ダッシュボードデータ取得完了: {year}年", context)

        return DashboardData(
            year=year,
            month_summaries=month_summaries,
            annual_gross=annual_gross,
            annual_net=annual_net,
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
