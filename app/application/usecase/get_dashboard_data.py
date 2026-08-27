"""ダッシュボードデータ取得ユースケース"""
from __future__ import annotations

from dataclasses import dataclass

from app.application.port.income_repository import IncomeRepository
from app.application.port.living_expense_repository import LivingExpenseRepository
from app.application.port.logger import Logger
from app.application.port.month_note_repository import MonthNoteRepository
from app.application.port.month_summary_repository import MonthSummaryRepository
from app.domain.model.living_expense import LIVING_EXPENSE_CATEGORIES
from app.domain.model.money import Money
from app.domain.model.month_note import MonthNote
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
    month_notes: dict[YearMonth, MonthNote]
    """月別メモ（平均以上／以下に消費した理由）"""
    variable_average: int
    """変動費の月平均（サマリのある月のみを対象）"""

    def living_total(self, ym: YearMonth) -> int:
        """指定年月の生活費合計を取得"""
        by_cat = self.living_expenses_by_month.get(ym, {})
        return sum(money.amount for money in by_cat.values())

    def variable_diff(self, ym: YearMonth) -> int:
        """指定年月の変動費と月平均との差（正なら平均以上）"""
        summary = next((s for s in self.month_summaries if s.year_month == ym), None)
        if summary is None:
            return 0
        return summary.variable_total.amount - self.variable_average

    def note_text(self, ym: YearMonth) -> str:
        """指定年月のメモ本文を取得（未登録の場合は空文字）"""
        note = self.month_notes.get(ym)
        return note.note if note else ""


class GetDashboardDataUseCase:
    """ダッシュボードデータ取得ユースケース"""

    def __init__(
        self,
        month_summary_repo: MonthSummaryRepository,
        income_repo: IncomeRepository,
        living_expense_repo: LivingExpenseRepository,
        month_note_repo: MonthNoteRepository,
        logger: Logger,
    ) -> None:
        self._month_summary_repo = month_summary_repo
        self._income_repo = income_repo
        self._living_expense_repo = living_expense_repo
        self._logger = logger
        self._month_note_repo = month_note_repo

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
        month_notes = await self._month_note_repo.find_by_year(year)
        variable_average = self._calculate_variable_average(month_summaries)

        self._logger.info(f"ダッシュボードデータ取得完了: {year}年", context)

        return DashboardData(
            year=year,
            month_summaries=month_summaries,
            annual_gross=annual_gross,
            annual_net=annual_net,
            living_expenses_by_month=living_expenses_by_month,
            month_notes=month_notes,
            variable_average=variable_average,
        )

    @staticmethod
    def _calculate_variable_average(month_summaries: list[MonthSummary]) -> int:
        """変動費の月平均を計算（サマリのある月のみを対象、小数は切り捨て）"""
        if not month_summaries:
            return 0
        total = sum(s.variable_total.amount for s in month_summaries)
        return total // len(month_summaries)

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
