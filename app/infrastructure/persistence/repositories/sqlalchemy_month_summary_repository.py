"""月次サマリのSQLAlchemy実装（暫定：集計は後続フェーズで実装）"""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.port.month_summary_repository import MonthSummaryRepository
from app.domain.model.month_summary import MonthSummary
from app.domain.model.year_month import YearMonth


class SqlAlchemyMonthSummaryRepository:
    """月次サマリのSQLAlchemy実装（暫定）"""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_year(self, year: int) -> list[MonthSummary]:
        """指定年の全月のサマリを取得（暫定：空リストを返す）"""
        # TODO: 後続フェーズで集計ロジックを実装
        return []

    async def find(self, ym: YearMonth) -> MonthSummary | None:
        """指定年月のサマリを取得（暫定：Noneを返す）"""
        # TODO: 後続フェーズで集計ロジックを実装
        return None


# Protocol実装として登録
MonthSummaryRepository.register(SqlAlchemyMonthSummaryRepository)

