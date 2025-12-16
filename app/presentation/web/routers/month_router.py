"""月次画面ルーター"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.port.cash_balance_repository import CashBalanceRepository
from app.application.port.card_repository import CardRepository
from app.application.port.card_statement_repository import CardStatementRepository
from app.application.port.fixed_item_history_repository import FixedItemHistoryRepository
from app.application.port.fixed_item_repository import FixedItemRepository
from app.application.port.income_repository import IncomeRepository
from app.application.port.logger import Logger
from app.application.port.withdrawal_repository import WithdrawalRepository
from app.application.usecase.get_month_summary import GetMonthSummaryUseCase
from app.application.usecase.manage_cash import (
    AddWithdrawalCommand,
    DeleteWithdrawalCommand,
    ManageCashUseCase,
    UpdateCashBalanceCommand,
)
from app.application.usecase.manage_cards import ManageCardsUseCase
from app.application.usecase.manage_fixed_items import (
    AddFixedItemCommand,
    AddFixedItemHistoryCommand,
    ManageFixedItemsUseCase,
)
from app.application.usecase.register_card_statements import (
    CardStatementCommand,
    RegisterCardStatementsUseCase,
)
from app.application.usecase.register_income import (
    RegisterIncomeCommand,
    RegisterIncomeUseCase,
)
from app.domain.model.year_month import YearMonth
from app.infrastructure.logging.structured_logger import StructuredLogger
from app.infrastructure.persistence.repositories.sqlalchemy_cash_balance_repository import (
    SqlAlchemyCashBalanceRepository,
)
from app.infrastructure.persistence.repositories.sqlalchemy_card_repository import (
    SqlAlchemyCardRepository,
)
from app.infrastructure.persistence.repositories.sqlalchemy_card_statement_repository import (
    SqlAlchemyCardStatementRepository,
)
from app.infrastructure.persistence.repositories.sqlalchemy_fixed_item_history_repository import (
    SqlAlchemyFixedItemHistoryRepository,
)
from app.infrastructure.persistence.repositories.sqlalchemy_fixed_item_repository import (
    SqlAlchemyFixedItemRepository,
)
from app.infrastructure.persistence.repositories.sqlalchemy_income_repository import (
    SqlAlchemyIncomeRepository,
)
from app.infrastructure.persistence.repositories.sqlalchemy_withdrawal_repository import (
    SqlAlchemyWithdrawalRepository,
)
from app.presentation.web.dependencies import get_db

router = APIRouter()


def provide_income_repo(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> IncomeRepository:
    """IncomeRepositoryのDI"""
    return SqlAlchemyIncomeRepository(session)


def provide_logger(request: Request) -> Logger:
    """LoggerのDI"""
    request_id = getattr(request.state, "request_id", None)
    return StructuredLogger("month", request_id)


def provide_register_income_uc(
    income_repo: Annotated[IncomeRepository, Depends(provide_income_repo)],
    logger: Annotated[Logger, Depends(provide_logger)],
) -> RegisterIncomeUseCase:
    """RegisterIncomeUseCaseのDI"""
    from app.application.usecase.register_income import RegisterIncomeUseCase

    return RegisterIncomeUseCase(income_repo=income_repo, logger=logger)


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


def provide_manage_fixed_items_uc(
    fixed_item_repo: Annotated[FixedItemRepository, Depends(provide_fixed_item_repo)],
    fixed_item_history_repo: Annotated[
        FixedItemHistoryRepository, Depends(provide_fixed_item_history_repo)
    ],
    logger: Annotated[Logger, Depends(provide_logger)],
) -> ManageFixedItemsUseCase:
    """ManageFixedItemsUseCaseのDI"""
    from app.application.usecase.manage_fixed_items import ManageFixedItemsUseCase

    return ManageFixedItemsUseCase(
        fixed_item_repo=fixed_item_repo,
        fixed_item_history_repo=fixed_item_history_repo,
        logger=logger,
    )


def provide_manage_cards_uc(
    card_repo: Annotated[CardRepository, Depends(provide_card_repo)],
    logger: Annotated[Logger, Depends(provide_logger)],
) -> ManageCardsUseCase:
    """ManageCardsUseCaseのDI"""
    from app.application.usecase.manage_cards import ManageCardsUseCase

    return ManageCardsUseCase(card_repo=card_repo, logger=logger)


def provide_cash_balance_repo(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> CashBalanceRepository:
    """CashBalanceRepositoryのDI"""
    return SqlAlchemyCashBalanceRepository(session)


def provide_withdrawal_repo(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> WithdrawalRepository:
    """WithdrawalRepositoryのDI"""
    return SqlAlchemyWithdrawalRepository(session)


def provide_manage_cash_uc(
    cash_balance_repo: Annotated[CashBalanceRepository, Depends(provide_cash_balance_repo)],
    withdrawal_repo: Annotated[WithdrawalRepository, Depends(provide_withdrawal_repo)],
    logger: Annotated[Logger, Depends(provide_logger)],
) -> ManageCashUseCase:
    """ManageCashUseCaseのDI"""
    from app.application.usecase.manage_cash import ManageCashUseCase

    return ManageCashUseCase(
        cash_balance_repo=cash_balance_repo,
        withdrawal_repo=withdrawal_repo,
        logger=logger,
    )


def provide_get_month_summary_uc(
    income_repo: Annotated[IncomeRepository, Depends(provide_income_repo)],
    fixed_item_history_repo: Annotated[
        FixedItemHistoryRepository, Depends(provide_fixed_item_history_repo)
    ],
    card_statement_repo: Annotated[
        CardStatementRepository, Depends(provide_card_statement_repo)
    ],
    cash_balance_repo: Annotated[CashBalanceRepository, Depends(provide_cash_balance_repo)],
    withdrawal_repo: Annotated[WithdrawalRepository, Depends(provide_withdrawal_repo)],
    card_repo: Annotated[CardRepository, Depends(provide_card_repo)],
    logger: Annotated[Logger, Depends(provide_logger)],
) -> GetMonthSummaryUseCase:
    """GetMonthSummaryUseCaseのDI"""
    from app.application.usecase.get_month_summary import GetMonthSummaryUseCase

    return GetMonthSummaryUseCase(
        income_repo=income_repo,
        fixed_item_history_repo=fixed_item_history_repo,
        card_statement_repo=card_statement_repo,
        cash_balance_repo=cash_balance_repo,
        withdrawal_repo=withdrawal_repo,
        card_repo=card_repo,
        logger=logger,
    )


def provide_card_statement_repo(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> CardStatementRepository:
    """CardStatementRepositoryのDI"""
    return SqlAlchemyCardStatementRepository(session)


def provide_register_card_statements_uc(
    card_statement_repo: Annotated[
        CardStatementRepository, Depends(provide_card_statement_repo)
    ],
    card_repo: Annotated[CardRepository, Depends(provide_card_repo)],
    logger: Annotated[Logger, Depends(provide_logger)],
) -> RegisterCardStatementsUseCase:
    """RegisterCardStatementsUseCaseのDI"""
    from app.application.usecase.register_card_statements import RegisterCardStatementsUseCase

    return RegisterCardStatementsUseCase(
        card_statement_repo=card_statement_repo,
        card_repo=card_repo,
        logger=logger,
    )


@router.get("/month/{year}/{month}", response_class=HTMLResponse)
async def month_page(
    request: Request,
    year: int,
    month: int,
    income_repo: Annotated[IncomeRepository, Depends(provide_income_repo)],
) -> HTMLResponse:
    """月次画面表示"""
    from datetime import datetime

    from fastapi.templating import Jinja2Templates

    templates = Jinja2Templates(directory="app/presentation/templates")

    # 年月のバリデーション
    try:
        ym = YearMonth(year, month)
    except ValueError:
        # 無効な年月の場合は現在年月にリダイレクト
        current = datetime.now()
        return HTMLResponse(
            content=f"<script>window.location.href='/month/{current.year}/{current.month}';</script>",
            status_code=400,
        )

    # 収入データを取得
    income = await income_repo.find(ym)

    # 前月・次月を計算
    prev_ym = YearMonth(year, month - 1) if month > 1 else YearMonth(year - 1, 12)
    next_ym = YearMonth(year, month + 1) if month < 12 else YearMonth(year + 1, 1)

    return templates.TemplateResponse(
        "month/index.html",
        {
            "request": request,
            "year": year,
            "month": month,
            "year_month": ym,
            "prev_year": prev_ym.year,
            "prev_month": prev_ym.month,
            "next_year": next_ym.year,
            "next_month": next_ym.month,
            "income": income,
        },
    )


@router.get("/month/{year}/{month}/tab/income", response_class=HTMLResponse)
async def income_tab(
    request: Request,
    year: int,
    month: int,
    income_repo: Annotated[IncomeRepository, Depends(provide_income_repo)],
) -> HTMLResponse:
    """収入タブコンテンツ"""
    from fastapi.templating import Jinja2Templates

    templates = Jinja2Templates(directory="app/presentation/templates")

    ym = YearMonth(year, month)
    income = await income_repo.find(ym)

    return templates.TemplateResponse(
        "month/income_tab.html",
        {
            "request": request,
            "year": year,
            "month": month,
            "income": income,
        },
    )


@router.post("/month/{year}/{month}/income", response_class=HTMLResponse)
async def register_income(
    request: Request,
    year: int,
    month: int,
    salary_gross: int = Form(...),
    salary_net: int = Form(...),
    bonus_gross: int = Form(default=0),
    bonus_net: int = Form(default=0),
    usecase: Annotated[RegisterIncomeUseCase, Depends(provide_register_income_uc)] = None,
    income_repo: Annotated[IncomeRepository, Depends(provide_income_repo)] = None,
) -> HTMLResponse:
    """収入登録"""
    from fastapi.templating import Jinja2Templates

    templates = Jinja2Templates(directory="app/presentation/templates")

    command = RegisterIncomeCommand(
        year=year,
        month=month,
        salary_gross=salary_gross,
        salary_net=salary_net,
        bonus_gross=bonus_gross,
        bonus_net=bonus_net,
    )
    await usecase.execute(command)

    # 収入タブを再取得
    ym = YearMonth(year, month)
    income = await income_repo.find(ym)

    return templates.TemplateResponse(
        "month/income_tab.html",
        {
            "request": request,
            "year": year,
            "month": month,
            "income": income,
        },
    )


@router.get("/month/{year}/{month}/tab/summary", response_class=HTMLResponse)
async def summary_tab(
    request: Request,
    year: int,
    month: int,
    summary_uc: Annotated[GetMonthSummaryUseCase, Depends(provide_get_month_summary_uc)] = None,
) -> HTMLResponse:
    """集計タブコンテンツ"""
    from fastapi.templating import Jinja2Templates

    templates = Jinja2Templates(directory="app/presentation/templates")

    result = await summary_uc.execute(year, month)

    return templates.TemplateResponse(
        "month/summary_tab.html",
        {
            "request": request,
            "year": year,
            "month": month,
            "summary": result.summary,
            "warnings": result.warnings,
            "cash_spent_uncertain": result.cash_spent_uncertain,
            "variable_card_negative": result.variable_card_negative,
        },
    )


@router.get("/month/{year}/{month}/tab/variable", response_class=HTMLResponse)
async def variable_tab(
    request: Request,
    year: int,
    month: int,
    card_statement_repo: Annotated[
        CardStatementRepository, Depends(provide_card_statement_repo)
    ] = None,
    cards_uc: Annotated[ManageCardsUseCase, Depends(provide_manage_cards_uc)] = None,
) -> HTMLResponse:
    """変動費タブコンテンツ"""
    from fastapi.templating import Jinja2Templates

    templates = Jinja2Templates(directory="app/presentation/templates")

    ym = YearMonth(year, month)
    statements = await card_statement_repo.find_by_year_month(ym)
    cards = await cards_uc.get_all_cards()

    return templates.TemplateResponse(
        "month/variable_tab.html",
        {
            "request": request,
            "year": year,
            "month": month,
            "statements": statements,
            "cards": cards,
        },
    )


@router.post("/month/{year}/{month}/card-statements", response_class=HTMLResponse)
async def register_card_statements(
    request: Request,
    year: int,
    month: int,
    usecase: Annotated[
        RegisterCardStatementsUseCase, Depends(provide_register_card_statements_uc)
    ] = None,
    card_statement_repo: Annotated[
        CardStatementRepository, Depends(provide_card_statement_repo)
    ] = None,
    cards_uc: Annotated[ManageCardsUseCase, Depends(provide_manage_cards_uc)] = None,
) -> HTMLResponse:
    """カード請求を登録"""
    from fastapi.templating import Jinja2Templates

    templates = Jinja2Templates(directory="app/presentation/templates")

    # フォームデータからカード請求コマンドのリストを作成
    form_data = await request.form()
    commands: list[CardStatementCommand] = []

    # フォームデータから card_id と amount のペアを抽出
    # フォームの構造: card_id_0, amount_0, card_id_1, amount_1, ...
    card_ids: list[int] = []
    amounts: list[int] = []

    for key, value in form_data.items():
        if key.startswith("card_id_"):
            idx = int(key.split("_")[-1])
            if value and value.strip():
                card_ids.append((idx, int(value)))
        elif key.startswith("amount_"):
            idx = int(key.split("_")[-1])
            if value and value.strip():
                amounts.append((idx, int(value)))

    # インデックスでソートしてペアを作成
    card_ids.sort(key=lambda x: x[0])
    amounts.sort(key=lambda x: x[0])

    # 同じインデックスのペアを作成
    max_idx = max(
        max([idx for idx, _ in card_ids], default=-1),
        max([idx for idx, _ in amounts], default=-1),
    )

    for i in range(max_idx + 1):
        card_id_val = next((cid for idx, cid in card_ids if idx == i), None)
        amount_val = next((amt for idx, amt in amounts if idx == i), None)

        if card_id_val is not None and amount_val is not None and amount_val > 0:
            commands.append(CardStatementCommand(card_id=card_id_val, amount=amount_val))

    await usecase.execute(year, month, commands)

    # 変動費タブを再取得
    ym = YearMonth(year, month)
    statements = await card_statement_repo.find_by_year_month(ym)
    cards = await cards_uc.get_all_cards()

    return templates.TemplateResponse(
        "month/variable_tab.html",
        {
            "request": request,
            "year": year,
            "month": month,
            "statements": statements,
            "cards": cards,
        },
    )


@router.get("/month/{year}/{month}/tab/cash", response_class=HTMLResponse)
async def cash_tab(
    request: Request,
    year: int,
    month: int,
    cash_uc: Annotated[ManageCashUseCase, Depends(provide_manage_cash_uc)] = None,
) -> HTMLResponse:
    """現金タブコンテンツ"""
    from fastapi.templating import Jinja2Templates

    templates = Jinja2Templates(directory="app/presentation/templates")

    cash_data = await cash_uc.get_cash_data(year, month)
    next_ym = YearMonth(year, month + 1) if month < 12 else YearMonth(year + 1, 1)

    return templates.TemplateResponse(
        "month/cash_tab.html",
        {
            "request": request,
            "year": year,
            "month": month,
            "cash_data": cash_data,
            "next_year": next_ym.year,
            "next_month": next_ym.month,
        },
    )


@router.post("/month/{year}/{month}/cash-balance", response_class=HTMLResponse)
async def save_cash_balance(
    request: Request,
    year: int,
    month: int,
    amount: int = Form(...),
    cash_uc: Annotated[ManageCashUseCase, Depends(provide_manage_cash_uc)] = None,
) -> HTMLResponse:
    """月初現金を保存"""
    from fastapi.templating import Jinja2Templates

    templates = Jinja2Templates(directory="app/presentation/templates")

    command = UpdateCashBalanceCommand(year=year, month=month, amount=amount)
    await cash_uc.update_cash_balance(command)

    # 現金タブを再取得
    cash_data = await cash_uc.get_cash_data(year, month)
    next_ym = YearMonth(year, month + 1) if month < 12 else YearMonth(year + 1, 1)

    return templates.TemplateResponse(
        "month/cash_tab.html",
        {
            "request": request,
            "year": year,
            "month": month,
            "cash_data": cash_data,
            "next_year": next_ym.year,
            "next_month": next_ym.month,
        },
    )


@router.post("/month/{year}/{month}/withdrawals", response_class=HTMLResponse)
async def save_withdrawal(
    request: Request,
    year: int,
    month: int,
    withdrawal_date: str = Form(...),
    amount: int = Form(...),
    note: str = Form(default=""),
    cash_uc: Annotated[ManageCashUseCase, Depends(provide_manage_cash_uc)] = None,
) -> HTMLResponse:
    """引出明細を保存"""
    from datetime import date as date_type
    from fastapi.templating import Jinja2Templates

    templates = Jinja2Templates(directory="app/presentation/templates")

    # 日付文字列をdateオブジェクトに変換
    withdrawal_date_obj = date_type.fromisoformat(withdrawal_date)

    command = AddWithdrawalCommand(
        year=year,
        month=month,
        withdrawal_date=withdrawal_date_obj,
        amount=amount,
        note=note,
    )
    await cash_uc.add_withdrawal(command)

    # 現金タブを再取得
    cash_data = await cash_uc.get_cash_data(year, month)
    next_ym = YearMonth(year, month + 1) if month < 12 else YearMonth(year + 1, 1)

    return templates.TemplateResponse(
        "month/cash_tab.html",
        {
            "request": request,
            "year": year,
            "month": month,
            "cash_data": cash_data,
            "next_year": next_ym.year,
            "next_month": next_ym.month,
        },
    )


@router.post("/month/{year}/{month}/cash-balance-next", response_class=HTMLResponse)
async def save_next_cash_balance(
    request: Request,
    year: int,
    month: int,
    next_year: int = Form(...),
    next_month: int = Form(...),
    amount: int = Form(...),
    cash_uc: Annotated[ManageCashUseCase, Depends(provide_manage_cash_uc)] = None,
) -> HTMLResponse:
    """次月月初現金を保存"""
    from fastapi.templating import Jinja2Templates

    templates = Jinja2Templates(directory="app/presentation/templates")

    command = UpdateCashBalanceCommand(year=next_year, month=next_month, amount=amount)
    await cash_uc.update_cash_balance(command)

    # 現金タブを再取得（当月のタブを更新）
    cash_data = await cash_uc.get_cash_data(year, month)
    next_ym = YearMonth(next_year, next_month)

    return templates.TemplateResponse(
        "month/cash_tab.html",
        {
            "request": request,
            "year": year,
            "month": month,
            "cash_data": cash_data,
            "next_year": next_ym.year,
            "next_month": next_ym.month,
        },
    )


@router.post("/month/{year}/{month}/withdrawals/{withdrawal_id}/delete", response_class=HTMLResponse)
async def delete_withdrawal(
    request: Request,
    year: int,
    month: int,
    withdrawal_id: int,
    cash_uc: Annotated[ManageCashUseCase, Depends(provide_manage_cash_uc)] = None,
) -> HTMLResponse:
    """引出明細を削除"""
    from fastapi.templating import Jinja2Templates

    templates = Jinja2Templates(directory="app/presentation/templates")

    command = DeleteWithdrawalCommand(withdrawal_id=withdrawal_id)
    await cash_uc.delete_withdrawal(command)

    # 現金タブを再取得
    cash_data = await cash_uc.get_cash_data(year, month)
    next_ym = YearMonth(year, month + 1) if month < 12 else YearMonth(year + 1, 1)

    return templates.TemplateResponse(
        "month/cash_tab.html",
        {
            "request": request,
            "year": year,
            "month": month,
            "cash_data": cash_data,
            "next_year": next_ym.year,
            "next_month": next_ym.month,
        },
    )


@router.get("/month/{year}/{month}/tab/fixed", response_class=HTMLResponse)
async def fixed_tab(
    request: Request,
    year: int,
    month: int,
    fixed_items_uc: Annotated[ManageFixedItemsUseCase, Depends(provide_manage_fixed_items_uc)] = None,
    cards_uc: Annotated[ManageCardsUseCase, Depends(provide_manage_cards_uc)] = None,
) -> HTMLResponse:
    """固定費タブコンテンツ"""
    from fastapi.templating import Jinja2Templates

    templates = Jinja2Templates(directory="app/presentation/templates")

    # 有効な固定費を取得
    active_items = await fixed_items_uc.get_active_fixed_items_at(year, month)

    # 全固定費項目を取得（履歴追加フォーム用）
    all_fixed_items = await fixed_items_uc.get_all_fixed_items()

    # カード一覧を取得（ドロップダウン用）
    cards = await cards_uc.get_all_cards()

    return templates.TemplateResponse(
        "month/fixed_tab.html",
        {
            "request": request,
            "year": year,
            "month": month,
            "active_items": active_items,
            "all_fixed_items": all_fixed_items,
            "cards": cards,
        },
    )


@router.post("/month/{year}/{month}/fixed-items", response_class=HTMLResponse)
async def add_fixed_item(
    request: Request,
    year: int,
    month: int,
    name: str = Form(...),
    fixed_items_uc: Annotated[ManageFixedItemsUseCase, Depends(provide_manage_fixed_items_uc)] = None,
    cards_uc: Annotated[ManageCardsUseCase, Depends(provide_manage_cards_uc)] = None,
) -> HTMLResponse:
    """固定費項目を追加"""
    from fastapi.templating import Jinja2Templates

    templates = Jinja2Templates(directory="app/presentation/templates")

    command = AddFixedItemCommand(name=name)
    await fixed_items_uc.add_fixed_item(command)

    # 固定費タブを再取得
    active_items = await fixed_items_uc.get_active_fixed_items_at(year, month)
    all_fixed_items = await fixed_items_uc.get_all_fixed_items()
    cards = await cards_uc.get_all_cards()

    return templates.TemplateResponse(
        "month/fixed_tab.html",
        {
            "request": request,
            "year": year,
            "month": month,
            "active_items": active_items,
            "all_fixed_items": all_fixed_items,
            "cards": cards,
        },
    )


@router.post("/month/{year}/{month}/fixed-item-histories", response_class=HTMLResponse)
async def add_fixed_item_history(
    request: Request,
    year: int,
    month: int,
    fixed_item_id: int = Form(...),
    effective_year: int = Form(...),
    effective_month: int = Form(...),
    amount: int = Form(...),
    card_id: str = Form(default=""),
    included_in_card: str = Form(default="false"),
    fixed_items_uc: Annotated[ManageFixedItemsUseCase, Depends(provide_manage_fixed_items_uc)] = None,
    cards_uc: Annotated[ManageCardsUseCase, Depends(provide_manage_cards_uc)] = None,
) -> HTMLResponse:
    """固定費履歴を追加"""
    from fastapi.templating import Jinja2Templates

    templates = Jinja2Templates(directory="app/presentation/templates")

    # card_idをintに変換（空文字列の場合はNone）
    card_id_int: int | None = None
    if card_id and card_id.strip():
        try:
            card_id_int = int(card_id)
        except ValueError:
            card_id_int = None

    # included_in_cardをboolに変換
    included_in_card_bool = included_in_card.lower() == "true"

    command = AddFixedItemHistoryCommand(
        fixed_item_id=fixed_item_id,
        year=effective_year,
        month=effective_month,
        amount=amount,
        card_id=card_id_int,
        included_in_card=included_in_card_bool,
    )
    await fixed_items_uc.add_fixed_item_history(command)

    # 固定費タブを再取得
    active_items = await fixed_items_uc.get_active_fixed_items_at(year, month)
    all_fixed_items = await fixed_items_uc.get_all_fixed_items()
    cards = await cards_uc.get_all_cards()

    return templates.TemplateResponse(
        "month/fixed_tab.html",
        {
            "request": request,
            "year": year,
            "month": month,
            "active_items": active_items,
            "all_fixed_items": all_fixed_items,
            "cards": cards,
        },
    )

