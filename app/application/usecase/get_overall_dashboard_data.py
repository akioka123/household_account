"""総合ダッシュボードデータ取得ユースケース"""
from __future__ import annotations

from dataclasses import dataclass

from app.application.port.income_repository import IncomeRepository
from app.application.port.logger import Logger
from app.application.port.month_summary_repository import MonthSummaryRepository
from app.domain.model.month_summary import MonthSummary


@dataclass(frozen=True)
class AnnualIncome:
    """年収データ"""

    year: int
    """対象年"""
    gross: int
    """年収（額面）"""
    net: int
    """年収（手取り）"""


@dataclass(frozen=True)
class OverallDashboardData:
    """総合ダッシュボード表示用データ"""

    annual_incomes: list[AnnualIncome]
    """年ごとの額面・手取り（2020年以降）"""
    month_summaries: list[MonthSummary]
    """月次サマリ一覧（2020年以降の全月）"""


class GetOverallDashboardDataUseCase:
    """総合ダッシュボードデータ取得ユースケース"""

    def __init__(
        self,
        month_summary_repo: MonthSummaryRepository,
        income_repo: IncomeRepository,
        logger: Logger,
    ) -> None:
        self._month_summary_repo = month_summary_repo
        self._income_repo = income_repo
        self._logger = logger

    async def execute(self, start_year: int = 2020, end_year: int = 2050) -> OverallDashboardData:
        """総合ダッシュボードデータを取得
        
        Args:
            start_year: 開始年（デフォルト: 2020）
            end_year: 終了年（デフォルト: 2050）
        
        Returns:
            総合ダッシュボード表示用データ
        """
        # ログ出力
        from app.domain.model.log_context import LogContext

        context = LogContext(screen="overall_dashboard", context={"start_year": start_year, "end_year": end_year})
        self._logger.info(f"総合ダッシュボードデータ取得開始: {start_year}年～{end_year}年", context)

        # 月別サマリを取得
        month_summaries = await self._month_summary_repo.find_by_years(start_year, end_year)

        # 年収データを取得・集計
        annual_incomes = await self._calculate_annual_incomes(start_year, end_year)

        self._logger.info(f"総合ダッシュボードデータ取得完了: {start_year}年～{end_year}年", context)

        return OverallDashboardData(
            annual_incomes=annual_incomes,
            month_summaries=month_summaries,
        )

    async def _calculate_annual_incomes(self, start_year: int, end_year: int) -> list[AnnualIncome]:
        """年収（額面・手取り）を計算"""
        # 指定期間の全月の収入を取得
        incomes = await self._income_repo.find_by_years(start_year, end_year)

        # 年ごとに集計
        annual_data: dict[int, tuple[int, int]] = {}  # {year: (gross_total, net_total)}
        
        for ym, income in incomes.items():
            if ym.year not in annual_data:
                annual_data[ym.year] = (0, 0)
            
            gross, net = annual_data[ym.year]
            annual_data[ym.year] = (
                gross + income.gross_total().amount,
                net + income.net_total().amount,
            )

        # 年順にソートしてAnnualIncomeリストを作成
        annual_incomes: list[AnnualIncome] = []
        for year in range(start_year, end_year + 1):
            if year in annual_data:
                gross, net = annual_data[year]
                annual_incomes.append(AnnualIncome(year=year, gross=gross, net=net))
            else:
                # データがない年も含める（グラフ上でnullとして表示）
                annual_incomes.append(AnnualIncome(year=year, gross=0, net=0))

        return annual_incomes
