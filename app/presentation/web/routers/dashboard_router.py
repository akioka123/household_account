"""ダッシュボードルーター"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.port.income_repository import IncomeRepository
from app.application.port.logger import Logger
from app.application.port.month_summary_repository import MonthSummaryRepository
from app.application.usecase.get_dashboard_data import GetDashboardDataUseCase
from app.infrastructure.logging.structured_logger import StructuredLogger
from app.infrastructure.persistence.repositories.sqlalchemy_income_repository import (
    SqlAlchemyIncomeRepository,
)
from app.infrastructure.persistence.repositories.sqlalchemy_month_summary_repository import (
    SqlAlchemyMonthSummaryRepository,
)
from app.presentation.web.dependencies import get_db
from app.presentation.web.helpers import get_years_with_data

router = APIRouter()


def provide_income_repo(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> IncomeRepository:
    """IncomeRepositoryのDI"""
    return SqlAlchemyIncomeRepository(session)


def provide_month_summary_repo(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> MonthSummaryRepository:
    """MonthSummaryRepositoryのDI"""
    return SqlAlchemyMonthSummaryRepository(session)


def provide_logger(request: Request) -> Logger:
    """LoggerのDI"""
    request_id = getattr(request.state, "request_id", None)
    return StructuredLogger("dashboard", request_id)


def provide_get_dashboard_data_uc(
    month_summary_repo: Annotated[MonthSummaryRepository, Depends(provide_month_summary_repo)],
    income_repo: Annotated[IncomeRepository, Depends(provide_income_repo)],
    logger: Annotated[Logger, Depends(provide_logger)],
) -> GetDashboardDataUseCase:
    """GetDashboardDataUseCaseのDI"""
    return GetDashboardDataUseCase(
        month_summary_repo=month_summary_repo,
        income_repo=income_repo,
        logger=logger,
    )


@router.get("/dashboard/{year}", response_class=HTMLResponse)
async def dashboard(
    year: int,
    request: Request,
    usecase: Annotated[GetDashboardDataUseCase, Depends(provide_get_dashboard_data_uc)],
) -> HTMLResponse:
    """ダッシュボード表示"""
    from datetime import datetime

    from fastapi.templating import Jinja2Templates

    templates = Jinja2Templates(directory="app/presentation/templates")

    # ダッシュボードデータを取得
    dashboard_data = await usecase.execute(year)

    # 年選択用のデータを準備
    current_year = datetime.now().year
    years_with_data = set()  # TODO: 後続フェーズで実装
    years = get_years_with_data(year, years_with_data)

    return templates.TemplateResponse(
        "dashboard/index.html",
        {
            "request": request,
            "year": year,
            "current_year": year,
            "years": years,
            "dashboard_data": dashboard_data,
        },
    )

