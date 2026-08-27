"""固定費棚卸し画面ルーター"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.port.card_repository import CardRepository
from app.application.port.fixed_item_history_repository import FixedItemHistoryRepository
from app.application.port.fixed_item_repository import FixedItemRepository
from app.application.port.logger import Logger
from app.application.usecase.get_fixed_items_overview import GetFixedItemsOverviewUseCase
from app.domain.model.year_month import YearMonth
from app.infrastructure.logging.structured_logger import StructuredLogger
from app.infrastructure.persistence.repositories.sqlalchemy_card_repository import (
    SqlAlchemyCardRepository,
)
from app.infrastructure.persistence.repositories.sqlalchemy_fixed_item_history_repository import (
    SqlAlchemyFixedItemHistoryRepository,
)
from app.infrastructure.persistence.repositories.sqlalchemy_fixed_item_repository import (
    SqlAlchemyFixedItemRepository,
)
from app.presentation.web.dependencies import get_db
from app.presentation.web.helpers import get_years_with_data

router = APIRouter()

templates = Jinja2Templates(directory="app/presentation/templates")


def provide_fixed_item_repo(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> FixedItemRepository:
    """FixedItemRepositoryのDI"""
    return SqlAlchemyFixedItemRepository(session)


def provide_fixed_item_history_repo(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> FixedItemHistoryRepository:
    """FixedItemHistoryRepositoryのDI"""
    return SqlAlchemyFixedItemHistoryRepository(session)


def provide_card_repo(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> CardRepository:
    """CardRepositoryのDI"""
    return SqlAlchemyCardRepository(session)


def provide_logger(request: Request) -> Logger:
    """LoggerのDI"""
    request_id = getattr(request.state, "request_id", None)
    return StructuredLogger("fixed_items", request_id)


def provide_get_fixed_items_overview_uc(
    fixed_item_repo: Annotated[FixedItemRepository, Depends(provide_fixed_item_repo)],
    fixed_item_history_repo: Annotated[
        FixedItemHistoryRepository, Depends(provide_fixed_item_history_repo)
    ],
    card_repo: Annotated[CardRepository, Depends(provide_card_repo)],
    logger: Annotated[Logger, Depends(provide_logger)],
) -> GetFixedItemsOverviewUseCase:
    """GetFixedItemsOverviewUseCaseのDI"""
    return GetFixedItemsOverviewUseCase(
        fixed_item_repo=fixed_item_repo,
        fixed_item_history_repo=fixed_item_history_repo,
        card_repo=card_repo,
        logger=logger,
    )


def parse_base_year_month(ym: str | None, now: datetime) -> YearMonth:
    """基準年月を解釈する

    不正な形式・範囲外の値は当月にフォールバックする。
    画面にエラー表示の仕組みが無いため、400を返さず当月を表示する方針。
    """
    if ym:
        try:
            return YearMonth.from_string(ym)
        except ValueError:
            pass
    return YearMonth(now.year, now.month)


@router.get("/fixed-items", response_class=HTMLResponse)
async def fixed_items_page(
    request: Request,
    usecase: Annotated[
        GetFixedItemsOverviewUseCase, Depends(provide_get_fixed_items_overview_uc)
    ],
    ym: str | None = None,
) -> HTMLResponse:
    """固定費棚卸し画面を表示

    htmxによる基準年月の切り替え時は本体部分のみを返す。
    """
    now = datetime.now()
    base_ym = parse_base_year_month(ym, now)

    overview = await usecase.execute(base_ym)

    template_name = (
        "fixed_items/content.html"
        if request.headers.get("HX-Request")
        else "fixed_items/index.html"
    )

    return templates.TemplateResponse(
        request,
        template_name,
        {
            "request": request,
            "current_year": now.year,
            "years": get_years_with_data(now.year, set()),
            "overview": overview,
            "base_year": base_ym.year,
            "base_month": base_ym.month,
        },
    )
