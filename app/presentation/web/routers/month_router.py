"""月次画面ルーター"""
from __future__ import annotations

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.port.cash_balance_repository import CashBalanceRepository
from app.application.port.card_repository import CardRepository
from app.application.port.card_statement_repository import CardStatementRepository
from app.application.port.fixed_item_history_repository import FixedItemHistoryRepository
from app.application.port.fixed_item_repository import FixedItemRepository
from app.application.port.income_repository import IncomeRepository
from app.application.port.living_expense_item_repository import LivingExpenseItemRepository
from app.application.port.logger import Logger
from app.application.port.living_expense_repository import LivingExpenseRepository
from app.application.port.month_note_repository import MonthNoteRepository
from app.application.port.receipt_image_storage import ReceiptImageStoragePort
from app.application.port.settings_repository import SettingsRepository
from app.application.port.withdrawal_repository import WithdrawalRepository
from app.application.usecase.get_month_summary import GetMonthSummaryUseCase
from app.application.usecase.manage_month_note import (
    ManageMonthNoteUseCase,
    SaveMonthNoteCommand,
)
from app.application.usecase.manage_cash import (
    AddWithdrawalCommand,
    DeleteWithdrawalCommand,
    ManageCashUseCase,
    UpdateCashBalanceCommand,
)
from app.application.usecase.manage_living_expenses import (
    AddLivingExpenseCommand,
    DeleteLivingExpenseCommand,
    LivingExpenseData,
    ManageLivingExpensesUseCase,
    UpdateLivingExpenseCommand,
)
from app.application.usecase.manage_living_expense_items import (
    AddLivingExpenseItemCommand,
    DeleteLivingExpenseItemCommand,
    DeleteReceiptCommand,
    ManageLivingExpenseItemsUseCase,
    UpdateLivingExpenseItemCommand,
)
from app.application.usecase.manage_cards import ManageCardsUseCase
from app.application.usecase.manage_fixed_items import (
    AddFixedItemCommand,
    AddFixedItemHistoryCommand,
    EndFixedItemOperationCommand,
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
from app.domain.model.living_expense import LIVING_EXPENSE_CATEGORIES, LIVING_EXPENSE_CATEGORY_FOOD
from app.domain.model.living_expense_item import (
    LIVING_EXPENSE_ITEM_SUBCATEGORIES,
    LIVING_EXPENSE_ITEM_SUBCATEGORY_LABELS,
)
from app.domain.model.year_month import YearMonth
from app.domain.service.receipt_paste_parser import ParsedReceiptLine
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
from app.infrastructure.persistence.repositories.sqlalchemy_living_expense_repository import (
    SqlAlchemyLivingExpenseRepository,
)
from app.infrastructure.persistence.repositories.sqlalchemy_living_expense_item_repository import (
    SqlAlchemyLivingExpenseItemRepository,
)
from app.infrastructure.persistence.repositories.sqlalchemy_month_note_repository import (
    SqlAlchemyMonthNoteRepository,
)
from app.infrastructure.persistence.repositories.sqlalchemy_settings_repository import (
    SqlAlchemySettingsRepository,
)
from app.infrastructure.persistence.repositories.sqlalchemy_withdrawal_repository import (
    SqlAlchemyWithdrawalRepository,
)
from app.infrastructure.storage.filesystem_receipt_image_storage import (
    FilesystemReceiptImageStorage,
)
from app.presentation.web.dependencies import get_db
from app.presentation.web.helpers import get_years_with_data

# プロジェクトルート（このファイルから見て5階層上）。レシート画像の配信に使用する
_PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent

router = APIRouter()

templates = Jinja2Templates(directory="app/presentation/templates")


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


def provide_settings_repo(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> SettingsRepository:
    """SettingsRepositoryのDI"""
    return SqlAlchemySettingsRepository(session)


def provide_manage_fixed_items_uc(
    fixed_item_repo: Annotated[FixedItemRepository, Depends(provide_fixed_item_repo)],
    fixed_item_history_repo: Annotated[
        FixedItemHistoryRepository, Depends(provide_fixed_item_history_repo)
    ],
    settings_repo: Annotated[SettingsRepository, Depends(provide_settings_repo)],
    logger: Annotated[Logger, Depends(provide_logger)],
) -> ManageFixedItemsUseCase:
    """ManageFixedItemsUseCaseのDI"""
    from app.application.usecase.manage_fixed_items import ManageFixedItemsUseCase

    return ManageFixedItemsUseCase(
        fixed_item_repo=fixed_item_repo,
        fixed_item_history_repo=fixed_item_history_repo,
        settings_repo=settings_repo,
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


# 生活費カテゴリの表示ラベル
LIVING_CATEGORY_LABELS = {
    "food": "食費",
    "electricity": "電気代",
    "gas": "ガス代",
    "mobile": "携帯料金",
    "communication": "通信費",
}


def provide_living_expense_repo(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> LivingExpenseRepository:
    """LivingExpenseRepositoryのDI"""
    return SqlAlchemyLivingExpenseRepository(session)


def provide_manage_living_expenses_uc(
    living_expense_repo: Annotated[LivingExpenseRepository, Depends(provide_living_expense_repo)],
    logger: Annotated[Logger, Depends(provide_logger)],
) -> ManageLivingExpensesUseCase:
    """ManageLivingExpensesUseCaseのDI"""
    return ManageLivingExpensesUseCase(
        living_expense_repo=living_expense_repo,
        logger=logger,
    )


def provide_living_expense_item_repo(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> LivingExpenseItemRepository:
    """LivingExpenseItemRepositoryのDI"""
    return SqlAlchemyLivingExpenseItemRepository(session)


def provide_receipt_image_storage() -> ReceiptImageStoragePort:
    """ReceiptImageStoragePortのDI"""
    return FilesystemReceiptImageStorage()


def provide_manage_living_expense_items_uc(
    living_expense_repo: Annotated[LivingExpenseRepository, Depends(provide_living_expense_repo)],
    living_expense_item_repo: Annotated[
        LivingExpenseItemRepository, Depends(provide_living_expense_item_repo)
    ],
    receipt_image_storage: Annotated[
        ReceiptImageStoragePort, Depends(provide_receipt_image_storage)
    ],
    logger: Annotated[Logger, Depends(provide_logger)],
) -> ManageLivingExpenseItemsUseCase:
    """ManageLivingExpenseItemsUseCaseのDI"""
    return ManageLivingExpenseItemsUseCase(
        living_expense_repo=living_expense_repo,
        living_expense_item_repo=living_expense_item_repo,
        receipt_image_storage=receipt_image_storage,
        logger=logger,
    )


def provide_month_note_repo(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> MonthNoteRepository:
    """MonthNoteRepositoryのDI"""
    return SqlAlchemyMonthNoteRepository(session)


def provide_manage_month_note_uc(
    month_note_repo: Annotated[MonthNoteRepository, Depends(provide_month_note_repo)],
    logger: Annotated[Logger, Depends(provide_logger)],
) -> ManageMonthNoteUseCase:
    """ManageMonthNoteUseCaseのDI"""
    return ManageMonthNoteUseCase(month_note_repo=month_note_repo, logger=logger)


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
    settings_repo: Annotated[SettingsRepository, Depends(provide_settings_repo)],
    logger: Annotated[Logger, Depends(provide_logger)],
) -> RegisterCardStatementsUseCase:
    """RegisterCardStatementsUseCaseのDI"""
    from app.application.usecase.register_card_statements import RegisterCardStatementsUseCase

    return RegisterCardStatementsUseCase(
        card_statement_repo=card_statement_repo,
        card_repo=card_repo,
        settings_repo=settings_repo,
        logger=logger,
    )


@router.get("/month/{year}/{month}", response_class=HTMLResponse)
async def month_page(
    request: Request,
    year: int,
    month: int,
    income_repo: Annotated[IncomeRepository, Depends(provide_income_repo)],
    summary_uc: Annotated[GetMonthSummaryUseCase, Depends(provide_get_month_summary_uc)],
    month_note_uc: Annotated[ManageMonthNoteUseCase, Depends(provide_manage_month_note_uc)],
) -> HTMLResponse:
    """月次画面表示"""
    from datetime import datetime

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

    # ヘッダー用のデータを準備
    current_year = datetime.now().year
    years_with_data = set()  # TODO: 後続フェーズで実装
    years = get_years_with_data(current_year, years_with_data)

    result = await summary_uc.execute(year, month)
    month_note = await month_note_uc.get_note(year, month)

    return templates.TemplateResponse(
        request,
        "month/index.html",
        {
            "request": request,
            "year": year,
            "month": month,
            "year_month": ym,
            "summary": result.summary,
            "warnings": result.warnings,
            "cash_spent_uncertain": result.cash_spent_uncertain,
            "variable_card_negative": result.variable_card_negative,
            "month_note": month_note,
            "prev_year": prev_ym.year,
            "prev_month": prev_ym.month,
            "next_year": next_ym.year,
            "next_month": next_ym.month,
            "income": income,
            "current_year": current_year,
            "years": years,
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
    ym = YearMonth(year, month)
    income = await income_repo.find(ym)

    return templates.TemplateResponse(
        request,
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
    usecase: Annotated[RegisterIncomeUseCase, Depends(provide_register_income_uc)],
    income_repo: Annotated[IncomeRepository, Depends(provide_income_repo)],
    salary_gross: int = Form(..., ge=0),
    salary_net: int = Form(..., ge=0),
    bonus_gross: int = Form(default=0, ge=0),
    bonus_net: int = Form(default=0, ge=0),
) -> HTMLResponse:
    """収入登録"""
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
        request,
        "month/income_tab.html",
        {
            "request": request,
            "year": year,
            "month": month,
            "income": income,
        },
    )


def _summary_tab_context(
    request: Request,
    year: int,
    month: int,
    result,
    month_note,
    note_error: str | None = None,
    note_saved: bool = False,
) -> dict:
    """集計タブ用テンプレートコンテキスト"""
    return {
        "request": request,
        "year": year,
        "month": month,
        "summary": result.summary,
        "warnings": result.warnings,
        "cash_spent_uncertain": result.cash_spent_uncertain,
        "variable_card_negative": result.variable_card_negative,
        "month_note": month_note,
        "note_error": note_error,
        "note_saved": note_saved,
    }


@router.get("/month/{year}/{month}/tab/summary", response_class=HTMLResponse)
async def summary_tab(
    request: Request,
    year: int,
    month: int,
    summary_uc: Annotated[GetMonthSummaryUseCase, Depends(provide_get_month_summary_uc)],
    month_note_uc: Annotated[ManageMonthNoteUseCase, Depends(provide_manage_month_note_uc)],
) -> HTMLResponse:
    """集計タブコンテンツ"""
    result = await summary_uc.execute(year, month)
    month_note = await month_note_uc.get_note(year, month)

    return templates.TemplateResponse(
        request,
        "month/summary_tab.html",
        _summary_tab_context(request, year, month, result, month_note),
    )


@router.post("/month/{year}/{month}/note", response_class=HTMLResponse)
async def save_month_note(
    request: Request,
    year: int,
    month: int,
    summary_uc: Annotated[GetMonthSummaryUseCase, Depends(provide_get_month_summary_uc)],
    month_note_uc: Annotated[ManageMonthNoteUseCase, Depends(provide_manage_month_note_uc)],
    note: str = Form(default=""),
) -> HTMLResponse:
    """月次メモ（平均以上／以下に消費した理由）を保存"""
    result = await summary_uc.execute(year, month)

    try:
        month_note = await month_note_uc.save_note(
            SaveMonthNoteCommand(year=year, month=month, note=note)
        )
    except ValueError as e:
        month_note = await month_note_uc.get_note(year, month)
        return templates.TemplateResponse(
            request,
            "month/summary_tab.html",
            _summary_tab_context(
                request, year, month, result, month_note, note_error=str(e)
            ),
        )

    return templates.TemplateResponse(
        request,
        "month/summary_tab.html",
        _summary_tab_context(request, year, month, result, month_note, note_saved=True),
    )


@router.get("/month/{year}/{month}/tab/variable", response_class=HTMLResponse)
async def variable_tab(
    request: Request,
    year: int,
    month: int,
    card_statement_repo: Annotated[
        CardStatementRepository, Depends(provide_card_statement_repo)
    ],
    cards_uc: Annotated[ManageCardsUseCase, Depends(provide_manage_cards_uc)],
) -> HTMLResponse:
    """変動費タブコンテンツ"""
    ym = YearMonth(year, month)
    statements = await card_statement_repo.find_by_year_month(ym)
    cards = await cards_uc.get_all_cards()

    return templates.TemplateResponse(
        request,
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
    ],
    card_statement_repo: Annotated[
        CardStatementRepository, Depends(provide_card_statement_repo)
    ],
    cards_uc: Annotated[ManageCardsUseCase, Depends(provide_manage_cards_uc)],
) -> HTMLResponse:
    """カード請求を登録"""
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

        if card_id_val is not None and amount_val is not None and amount_val >= 0:
            commands.append(CardStatementCommand(card_id=card_id_val, amount=amount_val))

    await usecase.execute(year, month, commands)

    # 変動費タブを再取得
    ym = YearMonth(year, month)
    statements = await card_statement_repo.find_by_year_month(ym)
    cards = await cards_uc.get_all_cards()

    return templates.TemplateResponse(
        request,
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
    cash_uc: Annotated[ManageCashUseCase, Depends(provide_manage_cash_uc)],
) -> HTMLResponse:
    """現金タブコンテンツ"""
    cash_data = await cash_uc.get_cash_data(year, month)
    next_ym = YearMonth(year, month + 1) if month < 12 else YearMonth(year + 1, 1)

    return templates.TemplateResponse(
        request,
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
    cash_uc: Annotated[ManageCashUseCase, Depends(provide_manage_cash_uc)],
    amount: int = Form(..., ge=0),
) -> HTMLResponse:
    """月初現金を保存"""
    command = UpdateCashBalanceCommand(year=year, month=month, amount=amount)
    await cash_uc.update_cash_balance(command)

    # 現金タブを再取得
    cash_data = await cash_uc.get_cash_data(year, month)
    next_ym = YearMonth(year, month + 1) if month < 12 else YearMonth(year + 1, 1)

    return templates.TemplateResponse(
        request,
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
    cash_uc: Annotated[ManageCashUseCase, Depends(provide_manage_cash_uc)],
    withdrawal_date: str = Form(...),
    amount: int = Form(..., ge=0),
    note: str = Form(default=""),
) -> HTMLResponse:
    """引出明細を保存"""
    from datetime import date as date_type
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
        request,
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
    cash_uc: Annotated[ManageCashUseCase, Depends(provide_manage_cash_uc)],
    next_year: int = Form(...),
    next_month: int = Form(...),
    amount: int = Form(..., ge=0),
) -> HTMLResponse:
    """次月月初現金を保存"""
    command = UpdateCashBalanceCommand(year=next_year, month=next_month, amount=amount)
    await cash_uc.update_cash_balance(command)

    # 現金タブを再取得（当月のタブを更新）
    cash_data = await cash_uc.get_cash_data(year, month)
    next_ym = YearMonth(next_year, next_month)

    return templates.TemplateResponse(
        request,
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
    cash_uc: Annotated[ManageCashUseCase, Depends(provide_manage_cash_uc)],
) -> HTMLResponse:
    """引出明細を削除"""
    command = DeleteWithdrawalCommand(withdrawal_id=withdrawal_id)
    await cash_uc.delete_withdrawal(command)

    # 現金タブを再取得
    cash_data = await cash_uc.get_cash_data(year, month)
    next_ym = YearMonth(year, month + 1) if month < 12 else YearMonth(year + 1, 1)

    return templates.TemplateResponse(
        request,
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
    fixed_items_uc: Annotated[ManageFixedItemsUseCase, Depends(provide_manage_fixed_items_uc)],
    cards_uc: Annotated[ManageCardsUseCase, Depends(provide_manage_cards_uc)],
) -> HTMLResponse:
    """固定費タブコンテンツ"""
    # 有効な固定費を取得
    active_items = await fixed_items_uc.get_active_fixed_items_at(year, month)

    # 全固定費項目を取得（履歴追加フォーム用）
    all_fixed_items = await fixed_items_uc.get_all_fixed_items()
    histories_by_item = await fixed_items_uc.get_histories_by_fixed_item(all_fixed_items)

    # カード一覧を取得（ドロップダウン用）
    cards = await cards_uc.get_all_cards()

    return templates.TemplateResponse(
        request,
        "month/fixed_tab.html",
        {
            "request": request,
            "year": year,
            "month": month,
            "active_items": active_items,
            "all_fixed_items": all_fixed_items,
            "histories_by_item": histories_by_item,
            "cards": cards,
        },
    )


@router.post("/month/{year}/{month}/fixed-items", response_class=HTMLResponse)
async def add_fixed_item(
    request: Request,
    year: int,
    month: int,
    fixed_items_uc: Annotated[ManageFixedItemsUseCase, Depends(provide_manage_fixed_items_uc)],
    cards_uc: Annotated[ManageCardsUseCase, Depends(provide_manage_cards_uc)],
    name: str = Form(...),
) -> HTMLResponse:
    """固定費項目を追加"""
    command = AddFixedItemCommand(name=name)
    await fixed_items_uc.add_fixed_item(command)

    # 固定費タブを再取得
    active_items = await fixed_items_uc.get_active_fixed_items_at(year, month)
    all_fixed_items = await fixed_items_uc.get_all_fixed_items()
    histories_by_item = await fixed_items_uc.get_histories_by_fixed_item(all_fixed_items)
    cards = await cards_uc.get_all_cards()

    return templates.TemplateResponse(
        request,
        "month/fixed_tab.html",
        {
            "request": request,
            "year": year,
            "month": month,
            "active_items": active_items,
            "all_fixed_items": all_fixed_items,
            "histories_by_item": histories_by_item,
            "cards": cards,
        },
    )


@router.post("/month/{year}/{month}/fixed-item-histories", response_class=HTMLResponse)
async def add_fixed_item_history(
    request: Request,
    year: int,
    month: int,
    fixed_items_uc: Annotated[ManageFixedItemsUseCase, Depends(provide_manage_fixed_items_uc)],
    cards_uc: Annotated[ManageCardsUseCase, Depends(provide_manage_cards_uc)],
    fixed_item_id: int = Form(...),
    effective_year: int = Form(...),
    effective_month: int = Form(...),
    amount: int = Form(..., ge=0),
    card_id: str = Form(default=""),
    included_in_card: str = Form(default="false"),
) -> HTMLResponse:
    """固定費履歴を追加"""
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
    histories_by_item = await fixed_items_uc.get_histories_by_fixed_item(all_fixed_items)
    cards = await cards_uc.get_all_cards()

    return templates.TemplateResponse(
        request,
        "month/fixed_tab.html",
        {
            "request": request,
            "year": year,
            "month": month,
            "active_items": active_items,
            "all_fixed_items": all_fixed_items,
            "histories_by_item": histories_by_item,
            "cards": cards,
        },
    )


@router.post(
    "/month/{year}/{month}/fixed-items/{fixed_item_id}/end",
    response_class=HTMLResponse,
)
async def end_fixed_item_operation(
    request: Request,
    year: int,
    month: int,
    fixed_item_id: int,
    fixed_items_uc: Annotated[ManageFixedItemsUseCase, Depends(provide_manage_fixed_items_uc)],
    cards_uc: Annotated[ManageCardsUseCase, Depends(provide_manage_cards_uc)],
    effective_year: int = Form(...),
    effective_month: int = Form(...),
) -> HTMLResponse:
    """固定費の運用を終了"""
    command = EndFixedItemOperationCommand(
        fixed_item_id=fixed_item_id,
        year=effective_year,
        month=effective_month,
    )
    await fixed_items_uc.end_fixed_item_operation(command)

    active_items = await fixed_items_uc.get_active_fixed_items_at(year, month)
    all_fixed_items = await fixed_items_uc.get_all_fixed_items()
    histories_by_item = await fixed_items_uc.get_histories_by_fixed_item(all_fixed_items)
    cards = await cards_uc.get_all_cards()

    return templates.TemplateResponse(
        request,
        "month/fixed_tab.html",
        {
            "request": request,
            "year": year,
            "month": month,
            "active_items": active_items,
            "all_fixed_items": all_fixed_items,
            "histories_by_item": histories_by_item,
            "cards": cards,
        },
    )


def _paste_preview_rows(lines: list[ParsedReceiptLine]) -> list[dict]:
    """貼り付けプレビュー行を編集フォーム用に整形する（表示用の整形はpresentation層）"""
    rows: list[dict] = []
    for line in lines:
        if line.error is None:
            rows.append(
                {
                    "name": line.name,
                    "amount": line.amount,
                    "sub_category_label": LIVING_EXPENSE_ITEM_SUBCATEGORY_LABELS.get(
                        line.sub_category or "", ""
                    ),
                    "error": None,
                }
            )
        else:
            # 解析に失敗した行も、可能な範囲で列に割り当てて再編集できるようにする
            parts = line.raw_line.split("\t")
            rows.append(
                {
                    "name": parts[0].strip() if len(parts) > 0 else line.raw_line,
                    "amount": parts[1].strip() if len(parts) > 1 else "",
                    "sub_category_label": parts[2].strip() if len(parts) > 2 else "",
                    "error": line.error,
                }
            )
    return rows


async def _living_tab_full_context(
    request: Request,
    year: int,
    month: int,
    living_expenses_uc: ManageLivingExpensesUseCase,
    living_items_uc: ManageLivingExpenseItemsUseCase,
    error_message: str | None = None,
    image_upload_error: str | None = None,
    active_receipt_id: int | None = None,
    paste_preview_receipt_id: int | None = None,
    paste_preview_lines: list[ParsedReceiptLine] | None = None,
    paste_error_message: str | None = None,
) -> dict:
    """生活費タブ用テンプレートコンテキスト（簡易入力・レシート一覧・小分類別集計）"""
    living_data = await living_expenses_uc.get_living_expense_data(year, month)
    receipts = await living_items_uc.get_receipts(year, month)
    sub_category_totals = await living_items_uc.get_sub_category_totals(year, month)

    # レシート経由で作成された食費（品目0件の新規作成直後を含む）は
    # 既存の簡易入力の食費一覧から除外する（基本設計3.3節）
    receipt_ids = {r.living_expense.id for r in receipts}
    filtered_food = [
        e
        for e in living_data.by_category.get(LIVING_EXPENSE_CATEGORY_FOOD, [])
        if e.id not in receipt_ids
    ]
    by_category = dict(living_data.by_category)
    by_category[LIVING_EXPENSE_CATEGORY_FOOD] = filtered_food
    filtered_living_data = LivingExpenseData(
        by_category=by_category,
        totals_by_category=living_data.totals_by_category,
    )

    items_by_receipt = {
        r.living_expense.id: await living_items_uc.get_items(r.living_expense.id)
        for r in receipts
    }

    return {
        "request": request,
        "year": year,
        "month": month,
        "living_data": filtered_living_data,
        "category_order": LIVING_EXPENSE_CATEGORIES,
        "category_labels": LIVING_CATEGORY_LABELS,
        "error_message": error_message,
        "image_upload_error": image_upload_error,
        "receipts": receipts,
        "items_by_receipt": items_by_receipt,
        "sub_category_totals": sub_category_totals,
        "sub_category_order": LIVING_EXPENSE_ITEM_SUBCATEGORIES,
        "sub_category_labels": LIVING_EXPENSE_ITEM_SUBCATEGORY_LABELS,
        "active_receipt_id": active_receipt_id,
        "paste_preview_receipt_id": paste_preview_receipt_id,
        "paste_preview_rows": _paste_preview_rows(paste_preview_lines)
        if paste_preview_lines is not None
        else None,
        "paste_error_message": paste_error_message,
    }


@router.get("/month/{year}/{month}/tab/living", response_class=HTMLResponse)
async def living_tab(
    request: Request,
    year: int,
    month: int,
    living_expenses_uc: Annotated[ManageLivingExpensesUseCase, Depends(provide_manage_living_expenses_uc)],
    living_items_uc: Annotated[
        ManageLivingExpenseItemsUseCase, Depends(provide_manage_living_expense_items_uc)
    ],
) -> HTMLResponse:
    """生活費タブコンテンツ"""
    context = await _living_tab_full_context(request, year, month, living_expenses_uc, living_items_uc)
    return templates.TemplateResponse(request, "month/living_tab.html", context)


@router.post("/month/{year}/{month}/living-expenses", response_class=HTMLResponse)
async def save_living_expense(
    request: Request,
    year: int,
    month: int,
    living_expenses_uc: Annotated[ManageLivingExpensesUseCase, Depends(provide_manage_living_expenses_uc)],
    living_items_uc: Annotated[
        ManageLivingExpenseItemsUseCase, Depends(provide_manage_living_expense_items_uc)
    ],
    category: str = Form(...),
    location: str = Form(default=""),
    amount: int = Form(..., ge=0),
    note: str = Form(default=""),
) -> HTMLResponse:
    """生活費を保存"""
    error_message: str | None = None
    try:
        command = AddLivingExpenseCommand(
            year=year,
            month=month,
            category=category,
            location=location,
            amount=amount,
            note=note,
        )
        await living_expenses_uc.add_living_expense(command)
    except ValueError as e:
        error_message = str(e)

    context = await _living_tab_full_context(
        request, year, month, living_expenses_uc, living_items_uc, error_message=error_message
    )
    return templates.TemplateResponse(request, "month/living_tab.html", context)


@router.post("/month/{year}/{month}/living-expenses/{living_expense_id}", response_class=HTMLResponse)
async def update_living_expense(
    request: Request,
    year: int,
    month: int,
    living_expense_id: int,
    living_expenses_uc: Annotated[ManageLivingExpensesUseCase, Depends(provide_manage_living_expenses_uc)],
    living_items_uc: Annotated[
        ManageLivingExpenseItemsUseCase, Depends(provide_manage_living_expense_items_uc)
    ],
    category: str = Form(...),
    location: str = Form(default=""),
    amount: int = Form(..., ge=0),
    note: str = Form(default=""),
) -> HTMLResponse:
    """生活費を更新"""
    error_message: str | None = None
    try:
        command = UpdateLivingExpenseCommand(
            living_expense_id=living_expense_id,
            year=year,
            month=month,
            category=category,
            location=location,
            amount=amount,
            note=note,
        )
        await living_expenses_uc.update_living_expense(command)
    except ValueError as e:
        error_message = str(e)

    context = await _living_tab_full_context(
        request, year, month, living_expenses_uc, living_items_uc, error_message=error_message
    )
    return templates.TemplateResponse(request, "month/living_tab.html", context)


@router.post("/month/{year}/{month}/living-expenses/{living_expense_id}/delete", response_class=HTMLResponse)
async def delete_living_expense(
    request: Request,
    year: int,
    month: int,
    living_expense_id: int,
    living_expenses_uc: Annotated[ManageLivingExpensesUseCase, Depends(provide_manage_living_expenses_uc)],
    living_items_uc: Annotated[
        ManageLivingExpenseItemsUseCase, Depends(provide_manage_living_expense_items_uc)
    ],
) -> HTMLResponse:
    """生活費を削除"""
    command = DeleteLivingExpenseCommand(living_expense_id=living_expense_id)
    await living_expenses_uc.delete_living_expense(command)

    context = await _living_tab_full_context(request, year, month, living_expenses_uc, living_items_uc)
    return templates.TemplateResponse(request, "month/living_tab.html", context)


@router.post("/month/{year}/{month}/receipts", response_class=HTMLResponse)
async def create_receipt(
    request: Request,
    year: int,
    month: int,
    living_expenses_uc: Annotated[ManageLivingExpensesUseCase, Depends(provide_manage_living_expenses_uc)],
    living_items_uc: Annotated[
        ManageLivingExpenseItemsUseCase, Depends(provide_manage_living_expense_items_uc)
    ],
) -> HTMLResponse:
    """レシートを新規作成する（画像なし、品目のみ）"""
    receipt = await living_items_uc.create_receipt(year, month)

    context = await _living_tab_full_context(
        request, year, month, living_expenses_uc, living_items_uc, active_receipt_id=receipt.id
    )
    return templates.TemplateResponse(request, "month/living_tab.html", context)


@router.post("/month/{year}/{month}/receipts/image", response_class=HTMLResponse)
async def create_receipt_with_image(
    request: Request,
    year: int,
    month: int,
    living_expenses_uc: Annotated[ManageLivingExpensesUseCase, Depends(provide_manage_living_expenses_uc)],
    living_items_uc: Annotated[
        ManageLivingExpenseItemsUseCase, Depends(provide_manage_living_expense_items_uc)
    ],
    image: UploadFile = File(...),
) -> HTMLResponse:
    """レシートを新規作成する（画像付き、multipart）"""
    data = await image.read()
    try:
        receipt = await living_items_uc.create_receipt_with_image(year, month, data)
    except ValueError as e:
        context = await _living_tab_full_context(
            request, year, month, living_expenses_uc, living_items_uc, image_upload_error=str(e)
        )
        return templates.TemplateResponse(request, "month/living_tab.html", context)

    context = await _living_tab_full_context(
        request, year, month, living_expenses_uc, living_items_uc, active_receipt_id=receipt.id
    )
    return templates.TemplateResponse(request, "month/living_tab.html", context)


@router.get("/month/{year}/{month}/receipts/{living_expense_id}/image")
async def get_receipt_image(
    year: int,
    month: int,
    living_expense_id: int,
    living_items_uc: Annotated[
        ManageLivingExpenseItemsUseCase, Depends(provide_manage_living_expense_items_uc)
    ],
) -> FileResponse:
    """保存済みレシート画像を返す"""
    receipt = await living_items_uc.get_receipt(living_expense_id)
    if receipt is None or not receipt.receipt_image_path:
        raise HTTPException(status_code=404, detail="画像が見つかりません")

    image_path = _PROJECT_ROOT / "data" / receipt.receipt_image_path
    if not image_path.exists():
        raise HTTPException(status_code=404, detail="画像が見つかりません")

    return FileResponse(image_path)


@router.post("/month/{year}/{month}/receipts/{living_expense_id}/delete", response_class=HTMLResponse)
async def delete_receipt(
    request: Request,
    year: int,
    month: int,
    living_expense_id: int,
    living_expenses_uc: Annotated[ManageLivingExpensesUseCase, Depends(provide_manage_living_expenses_uc)],
    living_items_uc: Annotated[
        ManageLivingExpenseItemsUseCase, Depends(provide_manage_living_expense_items_uc)
    ],
) -> HTMLResponse:
    """レシート（親＋品目全件＋画像ファイル）を削除する"""
    await living_items_uc.delete_receipt(DeleteReceiptCommand(living_expense_id=living_expense_id))

    context = await _living_tab_full_context(request, year, month, living_expenses_uc, living_items_uc)
    return templates.TemplateResponse(request, "month/living_tab.html", context)


@router.post("/month/{year}/{month}/receipts/{living_expense_id}/items", response_class=HTMLResponse)
async def add_receipt_item(
    request: Request,
    year: int,
    month: int,
    living_expense_id: int,
    living_expenses_uc: Annotated[ManageLivingExpensesUseCase, Depends(provide_manage_living_expenses_uc)],
    living_items_uc: Annotated[
        ManageLivingExpenseItemsUseCase, Depends(provide_manage_living_expense_items_uc)
    ],
    name: str = Form(...),
    amount: int = Form(...),
    sub_category: str = Form(...),
) -> HTMLResponse:
    """品目を1件追加する"""
    error_message: str | None = None
    try:
        await living_items_uc.add_item(
            AddLivingExpenseItemCommand(
                living_expense_id=living_expense_id,
                name=name,
                amount=amount,
                sub_category=sub_category,
            )
        )
    except ValueError as e:
        error_message = str(e)

    context = await _living_tab_full_context(
        request,
        year,
        month,
        living_expenses_uc,
        living_items_uc,
        active_receipt_id=living_expense_id,
        error_message=error_message,
    )
    return templates.TemplateResponse(request, "month/living_tab.html", context)


@router.post("/month/{year}/{month}/receipt-items/{item_id}", response_class=HTMLResponse)
async def update_receipt_item(
    request: Request,
    year: int,
    month: int,
    item_id: int,
    living_expenses_uc: Annotated[ManageLivingExpensesUseCase, Depends(provide_manage_living_expenses_uc)],
    living_items_uc: Annotated[
        ManageLivingExpenseItemsUseCase, Depends(provide_manage_living_expense_items_uc)
    ],
    living_expense_id: int = Form(...),
    name: str = Form(...),
    amount: int = Form(...),
    sub_category: str = Form(...),
) -> HTMLResponse:
    """品目を編集する"""
    error_message: str | None = None
    try:
        await living_items_uc.update_item(
            UpdateLivingExpenseItemCommand(
                item_id=item_id,
                living_expense_id=living_expense_id,
                name=name,
                amount=amount,
                sub_category=sub_category,
            )
        )
    except ValueError as e:
        error_message = str(e)

    context = await _living_tab_full_context(
        request,
        year,
        month,
        living_expenses_uc,
        living_items_uc,
        active_receipt_id=living_expense_id,
        error_message=error_message,
    )
    return templates.TemplateResponse(request, "month/living_tab.html", context)


@router.post("/month/{year}/{month}/receipt-items/{item_id}/delete", response_class=HTMLResponse)
async def delete_receipt_item(
    request: Request,
    year: int,
    month: int,
    item_id: int,
    living_expenses_uc: Annotated[ManageLivingExpensesUseCase, Depends(provide_manage_living_expenses_uc)],
    living_items_uc: Annotated[
        ManageLivingExpenseItemsUseCase, Depends(provide_manage_living_expense_items_uc)
    ],
    living_expense_id: int = Form(...),
) -> HTMLResponse:
    """品目を削除する"""
    await living_items_uc.delete_item(
        DeleteLivingExpenseItemCommand(item_id=item_id, living_expense_id=living_expense_id)
    )

    context = await _living_tab_full_context(
        request, year, month, living_expenses_uc, living_items_uc, active_receipt_id=living_expense_id
    )
    return templates.TemplateResponse(request, "month/living_tab.html", context)


@router.post(
    "/month/{year}/{month}/receipts/{living_expense_id}/items/paste-preview",
    response_class=HTMLResponse,
)
async def preview_receipt_paste(
    request: Request,
    year: int,
    month: int,
    living_expense_id: int,
    living_expenses_uc: Annotated[ManageLivingExpensesUseCase, Depends(provide_manage_living_expenses_uc)],
    living_items_uc: Annotated[
        ManageLivingExpenseItemsUseCase, Depends(provide_manage_living_expense_items_uc)
    ],
    paste_text: str = Form(...),
) -> HTMLResponse:
    """貼り付けテキストを解析してプレビューを表示する（保存は行わない）"""
    lines = living_items_uc.preview_paste(paste_text)

    context = await _living_tab_full_context(
        request,
        year,
        month,
        living_expenses_uc,
        living_items_uc,
        active_receipt_id=living_expense_id,
        paste_preview_receipt_id=living_expense_id,
        paste_preview_lines=lines,
    )
    return templates.TemplateResponse(request, "month/living_tab.html", context)


@router.post(
    "/month/{year}/{month}/receipts/{living_expense_id}/items/paste-save",
    response_class=HTMLResponse,
)
async def save_receipt_paste(
    request: Request,
    year: int,
    month: int,
    living_expense_id: int,
    living_expenses_uc: Annotated[ManageLivingExpensesUseCase, Depends(provide_manage_living_expenses_uc)],
    living_items_uc: Annotated[
        ManageLivingExpenseItemsUseCase, Depends(provide_manage_living_expense_items_uc)
    ],
) -> HTMLResponse:
    """貼り付けプレビューの編集後の全行を一括保存する（1行でも不正なら1件も保存しない）"""
    form_data = await request.form()
    names = form_data.getlist("name")
    amounts = form_data.getlist("amount")
    sub_category_labels = form_data.getlist("sub_category")

    if not (len(names) == len(amounts) == len(sub_category_labels)):
        # 品目名・金額・小分類の各リスト長が一致しない場合、zip()による暗黙の行欠落を避け
        # 保存せずエラー表示する（フォーム改ざん等の想定外入力に対する防御）
        context = await _living_tab_full_context(
            request,
            year,
            month,
            living_expenses_uc,
            living_items_uc,
            active_receipt_id=living_expense_id,
            error_message=(
                "送信されたデータの形式が不正です。もう一度貼り付けからやり直してください"
            ),
        )
        return templates.TemplateResponse(request, "month/living_tab.html", context)

    raw_text = "\n".join(
        f"{name}\t{amount}\t{sub_category_label}"
        for name, amount, sub_category_label in zip(names, amounts, sub_category_labels)
    )

    lines = await living_items_uc.save_paste(living_expense_id, raw_text)

    if any(line.error is not None for line in lines):
        context = await _living_tab_full_context(
            request,
            year,
            month,
            living_expenses_uc,
            living_items_uc,
            active_receipt_id=living_expense_id,
            paste_preview_receipt_id=living_expense_id,
            paste_preview_lines=lines,
            paste_error_message=(
                "一部の行が想定形式（品目名・金額・小分類）に一致しません。"
                "該当行を確認してください"
            ),
        )
        return templates.TemplateResponse(request, "month/living_tab.html", context)

    context = await _living_tab_full_context(
        request, year, month, living_expenses_uc, living_items_uc, active_receipt_id=living_expense_id
    )
    return templates.TemplateResponse(request, "month/living_tab.html", context)
