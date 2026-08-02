"""ダッシュボードルーター"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.port.income_repository import IncomeRepository
from app.application.port.living_expense_repository import LivingExpenseRepository
from app.application.port.logger import Logger
from app.application.port.month_summary_repository import MonthSummaryRepository
from app.application.usecase.get_dashboard_data import GetDashboardDataUseCase
from app.application.usecase.get_overall_dashboard_data import GetOverallDashboardDataUseCase
from app.infrastructure.logging.structured_logger import StructuredLogger
from app.infrastructure.persistence.repositories.sqlalchemy_living_expense_repository import (
    SqlAlchemyLivingExpenseRepository,
)
from app.infrastructure.persistence.repositories.sqlalchemy_income_repository import (
    SqlAlchemyIncomeRepository,
)
from app.infrastructure.persistence.repositories.sqlalchemy_month_summary_repository import (
    SqlAlchemyMonthSummaryRepository,
)
from app.domain.model.living_expense import LIVING_EXPENSE_CATEGORIES
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


def provide_living_expense_repo(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> LivingExpenseRepository:
    """LivingExpenseRepositoryのDI"""
    return SqlAlchemyLivingExpenseRepository(session)


def provide_get_dashboard_data_uc(
    month_summary_repo: Annotated[MonthSummaryRepository, Depends(provide_month_summary_repo)],
    income_repo: Annotated[IncomeRepository, Depends(provide_income_repo)],
    living_expense_repo: Annotated[LivingExpenseRepository, Depends(provide_living_expense_repo)],
    logger: Annotated[Logger, Depends(provide_logger)],
) -> GetDashboardDataUseCase:
    """GetDashboardDataUseCaseのDI"""
    return GetDashboardDataUseCase(
        month_summary_repo=month_summary_repo,
        income_repo=income_repo,
        living_expense_repo=living_expense_repo,
        logger=logger,
    )


def provide_get_overall_dashboard_data_uc(
    month_summary_repo: Annotated[MonthSummaryRepository, Depends(provide_month_summary_repo)],
    income_repo: Annotated[IncomeRepository, Depends(provide_income_repo)],
    logger: Annotated[Logger, Depends(provide_logger)],
) -> GetOverallDashboardDataUseCase:
    """GetOverallDashboardDataUseCaseのDI"""
    return GetOverallDashboardDataUseCase(
        month_summary_repo=month_summary_repo,
        income_repo=income_repo,
        logger=logger,
    )


@router.get("/dashboard/overall", response_class=HTMLResponse)
async def overall_dashboard(
    request: Request,
    usecase: Annotated[GetOverallDashboardDataUseCase, Depends(provide_get_overall_dashboard_data_uc)],
) -> HTMLResponse:
    """総合ダッシュボード表示"""
    from datetime import datetime

    from fastapi.templating import Jinja2Templates

    templates = Jinja2Templates(directory="app/presentation/templates")

    # 年選択用のデータを準備（年次ダッシュボード用）
    current_year = datetime.now().year
    start_year = current_year - 5  # 当年の5年前から
    
    # 総合ダッシュボードデータを取得（当年の5年前から当年まで）
    overall_dashboard_data = await usecase.execute(start_year=start_year, end_year=current_year)
    
    years_with_data = set()  # TODO: 後続フェーズで実装
    years = get_years_with_data(current_year, years_with_data)

    return templates.TemplateResponse(
        "dashboard/overall.html",
        {
            "request": request,
            "current_year": current_year,
            "start_year": start_year,
            "end_year": current_year,
            "years": years,
            "overall_dashboard_data": overall_dashboard_data,
        },
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

    LIVING_CATEGORY_LABELS = {
        "food": "食費",
        "electricity": "電気代",
        "gas": "ガス代",
        "mobile": "携帯料金",
        "communication": "通信費",
    }

    return templates.TemplateResponse(
        "dashboard/index.html",
        {
            "request": request,
            "year": year,
            "current_year": current_year,
            "years": years,
            "dashboard_data": dashboard_data,
            "living_category_order": LIVING_EXPENSE_CATEGORIES,
            "living_category_labels": LIVING_CATEGORY_LABELS,
        },
    )

