"""GetDashboardDataUseCaseのテスト"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.port.income_repository import IncomeRepository
from app.application.port.logger import Logger
from app.application.port.month_summary_repository import MonthSummaryRepository
from app.application.usecase.get_dashboard_data import (
    DashboardData,
    GetDashboardDataUseCase,
)
from app.domain.model.income import Income
from app.domain.model.money import Money
from app.domain.model.month_summary import MonthSummary
from app.domain.model.year_month import YearMonth


@pytest.fixture
def fake_month_summary_repo() -> MonthSummaryRepository:
    """Fake MonthSummaryRepository"""
    repo = MagicMock(spec=MonthSummaryRepository)
    repo.find_by_year = AsyncMock(return_value=[])
    return repo


@pytest.fixture
def fake_income_repo() -> IncomeRepository:
    """Fake IncomeRepository"""
    repo = MagicMock(spec=IncomeRepository)
    repo.find_by_year = AsyncMock(return_value={})
    return repo


@pytest.fixture
def fake_logger() -> Logger:
    """Fake Logger"""
    logger = MagicMock(spec=Logger)
    logger.info = MagicMock()
    return logger


@pytest.mark.asyncio
async def test_get_dashboard_data_empty(
    fake_month_summary_repo: MonthSummaryRepository,
    fake_income_repo: IncomeRepository,
    fake_logger: Logger,
) -> None:
    """データが空の場合のダッシュボードデータ取得"""
    usecase = GetDashboardDataUseCase(
        month_summary_repo=fake_month_summary_repo,
        income_repo=fake_income_repo,
        logger=fake_logger,
    )

    result = await usecase.execute(2024)

    assert result.year == 2024
    assert result.month_summaries == []
    assert result.annual_gross == 0
    assert result.annual_net == 0


@pytest.mark.asyncio
async def test_get_dashboard_data_with_data(
    fake_month_summary_repo: MonthSummaryRepository,
    fake_income_repo: IncomeRepository,
    fake_logger: Logger,
) -> None:
    """データがある場合のダッシュボードデータ取得"""
    # モックデータ設定
    ym1 = YearMonth(2024, 1)
    ym2 = YearMonth(2024, 2)
    summary1 = MonthSummary(
        year_month=ym1,
        net_income=Money(400000),
        fixed_total=Money(100000),
        variable_total=Money(150000),
        profit=Money(150000),
    )
    summary2 = MonthSummary(
        year_month=ym2,
        net_income=Money(400000),
        fixed_total=Money(100000),
        variable_total=Money(200000),
        profit=Money(100000),
    )
    fake_month_summary_repo.find_by_year = AsyncMock(
        return_value=[summary1, summary2]
    )

    income1 = Income.of(
        salary_gross=500000,
        salary_net=400000,
        bonus_gross=0,
        bonus_net=0,
    )
    income2 = Income.of(
        salary_gross=500000,
        salary_net=400000,
        bonus_gross=1000000,
        bonus_net=800000,
    )
    fake_income_repo.find_by_year = AsyncMock(
        return_value={ym1: income1, ym2: income2}
    )

    usecase = GetDashboardDataUseCase(
        month_summary_repo=fake_month_summary_repo,
        income_repo=fake_income_repo,
        logger=fake_logger,
    )

    result = await usecase.execute(2024)

    assert result.year == 2024
    assert len(result.month_summaries) == 2
    assert result.annual_gross == 2000000  # 500000 * 2 + 1000000
    assert result.annual_net == 1600000  # 400000 * 2 + 800000

