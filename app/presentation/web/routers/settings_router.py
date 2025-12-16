"""設定画面ルーター"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.port.card_repository import CardRepository
from app.application.port.logger import Logger
from app.application.port.settings_repository import SettingsRepository
from app.application.usecase.manage_cards import (
    CreateCardCommand,
    ManageCardsUseCase,
    UpdateCardCommand,
)
from app.application.usecase.update_limits import UpdateLimitsCommand, UpdateLimitsUseCase
from app.infrastructure.logging.structured_logger import StructuredLogger
from app.infrastructure.persistence.repositories.sqlalchemy_card_repository import (
    SqlAlchemyCardRepository,
)
from app.infrastructure.persistence.repositories.sqlalchemy_settings_repository import (
    SqlAlchemySettingsRepository,
)
from app.presentation.web.dependencies import get_db
from app.presentation.web.helpers import get_years_with_data

router = APIRouter()


def provide_card_repo(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> CardRepository:
    """CardRepositoryのDI"""
    return SqlAlchemyCardRepository(session)


def provide_settings_repo(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> SettingsRepository:
    """SettingsRepositoryのDI"""
    return SqlAlchemySettingsRepository(session)


def provide_logger(request: Request) -> Logger:
    """LoggerのDI"""
    request_id = getattr(request.state, "request_id", None)
    return StructuredLogger("settings", request_id)


def provide_manage_cards_uc(
    card_repo: Annotated[CardRepository, Depends(provide_card_repo)],
    logger: Annotated[Logger, Depends(provide_logger)],
) -> ManageCardsUseCase:
    """ManageCardsUseCaseのDI"""
    from app.application.usecase.manage_cards import ManageCardsUseCase

    return ManageCardsUseCase(card_repo=card_repo, logger=logger)


def provide_update_limits_uc(
    settings_repo: Annotated[SettingsRepository, Depends(provide_settings_repo)],
    logger: Annotated[Logger, Depends(provide_logger)],
) -> UpdateLimitsUseCase:
    """UpdateLimitsUseCaseのDI"""
    from app.application.usecase.update_limits import UpdateLimitsUseCase

    return UpdateLimitsUseCase(settings_repo=settings_repo, logger=logger)


@router.get("/settings", response_class=HTMLResponse)
async def settings_page(
    request: Request,
    card_uc: Annotated[ManageCardsUseCase, Depends(provide_manage_cards_uc)],
    limits_uc: Annotated[UpdateLimitsUseCase, Depends(provide_update_limits_uc)],
    settings_repo: Annotated[SettingsRepository, Depends(provide_settings_repo)],
) -> HTMLResponse:
    """設定画面表示"""
    from datetime import datetime

    from fastapi.templating import Jinja2Templates

    templates = Jinja2Templates(directory="app/presentation/templates")

    # カード一覧を取得
    cards = await card_uc.get_all_cards()

    # 設定を取得
    settings = await settings_repo.find()

    # 年選択用のデータを準備
    current_year = datetime.now().year
    years = get_years_with_data(current_year, set())

    return templates.TemplateResponse(
        "settings/index.html",
        {
            "request": request,
            "current_year": current_year,
            "years": years,
            "cards": cards,
            "settings": settings,
        },
    )


@router.post("/settings/cards", response_class=HTMLResponse)
async def create_card(
    request: Request,
    name: str = Form(...),
    card_uc: Annotated[ManageCardsUseCase, Depends(provide_manage_cards_uc)],
) -> HTMLResponse:
    """カード作成"""
    from fastapi.templating import Jinja2Templates

    templates = Jinja2Templates(directory="app/presentation/templates")

    command = CreateCardCommand(name=name)
    await card_uc.create_card(command)

    # カード一覧を再取得
    cards = await card_uc.get_all_cards()

    return templates.TemplateResponse(
        "settings/cards_tab.html",
        {"request": request, "cards": cards},
    )


@router.post("/settings/cards/{card_id}/toggle", response_class=HTMLResponse)
async def toggle_card(
    request: Request,
    card_id: int,
    card_uc: Annotated[ManageCardsUseCase, Depends(provide_manage_cards_uc)],
) -> HTMLResponse:
    """カードの有効/無効を切り替え"""
    from fastapi.templating import Jinja2Templates

    templates = Jinja2Templates(directory="app/presentation/templates")

    # カードを取得して現在の状態を確認
    cards = await card_uc.get_all_cards()
    card = next((c for c in cards if c.id == card_id), None)
    if card is None:
        # カードが見つからない場合はエラーを返す（簡易実装）
        cards = await card_uc.get_all_cards()
        return templates.TemplateResponse(
            "settings/cards_tab.html",
            {"request": request, "cards": cards},
        )

    # 有効/無効を切り替え
    command = UpdateCardCommand(card_id=card_id, enabled=not card.enabled)
    await card_uc.update_card(command)

    # カード一覧を再取得
    cards = await card_uc.get_all_cards()

    return templates.TemplateResponse(
        "settings/cards_tab.html",
        {"request": request, "cards": cards},
    )


@router.post("/settings/limits", response_class=HTMLResponse)
async def update_limits(
    request: Request,
    max_variable_items: int = Form(...),
    max_fixed_items: int = Form(...),
    limits_uc: Annotated[UpdateLimitsUseCase, Depends(provide_update_limits_uc)],
) -> HTMLResponse:
    """上限設定更新"""
    from fastapi.templating import Jinja2Templates

    templates = Jinja2Templates(directory="app/presentation/templates")

    command = UpdateLimitsCommand(
        max_variable_items=max_variable_items,
        max_fixed_items=max_fixed_items,
    )
    settings = await limits_uc.execute(command)

    return templates.TemplateResponse(
        "settings/limits_tab.html",
        {"request": request, "settings": settings},
    )

