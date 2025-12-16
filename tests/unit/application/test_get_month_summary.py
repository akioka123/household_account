"""GetMonthSummaryUseCaseのテスト"""
from __future__ import annotations

from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.port.cash_balance_repository import CashBalanceRepository
from app.application.port.card_repository import CardRepository
from app.application.port.card_statement_repository import CardStatementRepository
from app.application.port.fixed_item_history_repository import FixedItemHistoryRepository
from app.application.port.income_repository import IncomeRepository
from app.application.port.logger import Logger
from app.application.port.withdrawal_repository import WithdrawalRepository
from app.application.usecase.get_month_summary import (
    GetMonthSummaryUseCase,
    MonthSummaryResult,
)
from app.domain.model.cash_balance import CashBalance
from app.domain.model.card_statement import CardStatement
from app.domain.model.fixed_item_history import FixedItemHistory
from app.domain.model.income import Income
from app.domain.model.money import Money
from app.domain.model.withdrawal import Withdrawal
from app.domain.model.year_month import YearMonth


@pytest.fixture
def fake_income_repo() -> IncomeRepository:
    """Fake IncomeRepository"""
    repo = MagicMock(spec=IncomeRepository)
    repo.find = AsyncMock(return_value=None)
    return repo


@pytest.fixture
def fake_fixed_item_history_repo() -> FixedItemHistoryRepository:
    """Fake FixedItemHistoryRepository"""
    repo = MagicMock(spec=FixedItemHistoryRepository)
    repo.find_active_at = AsyncMock(return_value=[])
    return repo


@pytest.fixture
def fake_card_statement_repo() -> CardStatementRepository:
    """Fake CardStatementRepository"""
    repo = MagicMock(spec=CardStatementRepository)
    repo.find_by_year_month = AsyncMock(return_value=[])
    return repo


@pytest.fixture
def fake_cash_balance_repo() -> CashBalanceRepository:
    """Fake CashBalanceRepository"""
    repo = MagicMock(spec=CashBalanceRepository)
    repo.find = AsyncMock(return_value=None)
    return repo


@pytest.fixture
def fake_withdrawal_repo() -> WithdrawalRepository:
    """Fake WithdrawalRepository"""
    repo = MagicMock(spec=WithdrawalRepository)
    repo.find_by_year_month = AsyncMock(return_value=[])
    return repo


@pytest.fixture
def fake_card_repo() -> CardRepository:
    """Fake CardRepository"""
    repo = MagicMock(spec=CardRepository)
    return repo


@pytest.fixture
def fake_logger() -> Logger:
    """Fake Logger"""
    logger = MagicMock(spec=Logger)
    logger.info = MagicMock()
    return logger


@pytest.mark.asyncio
async def test_get_month_summary_basic(
    fake_income_repo: IncomeRepository,
    fake_fixed_item_history_repo: FixedItemHistoryRepository,
    fake_card_statement_repo: CardStatementRepository,
    fake_cash_balance_repo: CashBalanceRepository,
    fake_withdrawal_repo: WithdrawalRepository,
    fake_card_repo: CardRepository,
    fake_logger: Logger,
) -> None:
    """基本的な月次サマリ取得"""
    # 収入を設定
    income = Income.of(
        salary_gross=500000,
        salary_net=400000,
        bonus_gross=0,
        bonus_net=0,
    )
    fake_income_repo.find = AsyncMock(return_value=income)

    usecase = GetMonthSummaryUseCase(
        income_repo=fake_income_repo,
        fixed_item_history_repo=fake_fixed_item_history_repo,
        card_statement_repo=fake_card_statement_repo,
        cash_balance_repo=fake_cash_balance_repo,
        withdrawal_repo=fake_withdrawal_repo,
        card_repo=fake_card_repo,
        logger=fake_logger,
    )

    result = await usecase.execute(2024, 5)

    assert isinstance(result, MonthSummaryResult)
    assert result.summary.year_month == YearMonth(2024, 5)
    assert result.summary.net_income.amount == 400000
    assert result.summary.fixed_total.amount == 0
    assert result.summary.variable_total.amount == 0
    assert result.summary.profit.amount == 400000
    assert len(result.warnings) == 0
    assert result.cash_spent_uncertain is False
    assert result.variable_card_negative is False


@pytest.mark.asyncio
async def test_get_month_summary_with_fixed_items(
    fake_income_repo: IncomeRepository,
    fake_fixed_item_history_repo: FixedItemHistoryRepository,
    fake_card_statement_repo: CardStatementRepository,
    fake_cash_balance_repo: CashBalanceRepository,
    fake_withdrawal_repo: WithdrawalRepository,
    fake_card_repo: CardRepository,
    fake_logger: Logger,
) -> None:
    """固定費がある場合の月次サマリ取得"""
    income = Income.of(
        salary_gross=500000,
        salary_net=400000,
        bonus_gross=0,
        bonus_net=0,
    )
    fake_income_repo.find = AsyncMock(return_value=income)

    # 固定費履歴を設定
    fixed_history = FixedItemHistory(
        id=1,
        fixed_item_id=1,
        effective_from=YearMonth(2024, 1),
        amount=Money(100000),
        card_id=None,
        included_in_card=False,
    )
    fake_fixed_item_history_repo.find_active_at = AsyncMock(return_value=[fixed_history])

    usecase = GetMonthSummaryUseCase(
        income_repo=fake_income_repo,
        fixed_item_history_repo=fake_fixed_item_history_repo,
        card_statement_repo=fake_card_statement_repo,
        cash_balance_repo=fake_cash_balance_repo,
        withdrawal_repo=fake_withdrawal_repo,
        card_repo=fake_card_repo,
        logger=fake_logger,
    )

    result = await usecase.execute(2024, 5)

    assert result.summary.fixed_total.amount == 100000
    assert result.summary.profit.amount == 300000  # 400000 - 100000


@pytest.mark.asyncio
async def test_get_month_summary_with_card_statements(
    fake_income_repo: IncomeRepository,
    fake_fixed_item_history_repo: FixedItemHistoryRepository,
    fake_card_statement_repo: CardStatementRepository,
    fake_cash_balance_repo: CashBalanceRepository,
    fake_withdrawal_repo: WithdrawalRepository,
    fake_card_repo: CardRepository,
    fake_logger: Logger,
) -> None:
    """カード請求がある場合の月次サマリ取得"""
    income = Income.of(
        salary_gross=500000,
        salary_net=400000,
        bonus_gross=0,
        bonus_net=0,
    )
    fake_income_repo.find = AsyncMock(return_value=income)

    # カード請求を設定
    card_statement = CardStatement(
        id=1,
        year_month=YearMonth(2024, 5),
        card_id=1,
        amount=Money(50000),
    )
    fake_card_statement_repo.find_by_year_month = AsyncMock(return_value=[card_statement])

    usecase = GetMonthSummaryUseCase(
        income_repo=fake_income_repo,
        fixed_item_history_repo=fake_fixed_item_history_repo,
        card_statement_repo=fake_card_statement_repo,
        cash_balance_repo=fake_cash_balance_repo,
        withdrawal_repo=fake_withdrawal_repo,
        card_repo=fake_card_repo,
        logger=fake_logger,
    )

    result = await usecase.execute(2024, 5)

    assert result.summary.variable_total.amount == 50000
    assert result.summary.profit.amount == 350000  # 400000 - 50000


@pytest.mark.asyncio
async def test_get_month_summary_with_cash(
    fake_income_repo: IncomeRepository,
    fake_fixed_item_history_repo: FixedItemHistoryRepository,
    fake_card_statement_repo: CardStatementRepository,
    fake_cash_balance_repo: CashBalanceRepository,
    fake_withdrawal_repo: WithdrawalRepository,
    fake_card_repo: CardRepository,
    fake_logger: Logger,
) -> None:
    """現金支出がある場合の月次サマリ取得"""
    income = Income.of(
        salary_gross=500000,
        salary_net=400000,
        bonus_gross=0,
        bonus_net=0,
    )
    fake_income_repo.find = AsyncMock(return_value=income)

    # 月初現金と次月月初現金を設定
    cash_start = CashBalance(
        id=1,
        year_month=YearMonth(2024, 5),
        amount=Money(100000),
    )
    next_cash_start = CashBalance(
        id=2,
        year_month=YearMonth(2024, 6),
        amount=Money(50000),
    )
    fake_cash_balance_repo.find = AsyncMock(side_effect=[cash_start, next_cash_start])

    # 引出を設定
    withdrawal = Withdrawal(
        id=1,
        year_month=YearMonth(2024, 5),
        withdrawal_date=date(2024, 5, 15),
        amount=Money(20000),
        note="",
    )
    fake_withdrawal_repo.find_by_year_month = AsyncMock(return_value=[withdrawal])

    usecase = GetMonthSummaryUseCase(
        income_repo=fake_income_repo,
        fixed_item_history_repo=fake_fixed_item_history_repo,
        card_statement_repo=fake_card_statement_repo,
        cash_balance_repo=fake_cash_balance_repo,
        withdrawal_repo=fake_withdrawal_repo,
        card_repo=fake_card_repo,
        logger=fake_logger,
    )

    result = await usecase.execute(2024, 5)

    # 現金支出 = 100000 + 20000 - 50000 = 70000
    assert result.summary.variable_total.amount == 70000
    assert result.summary.profit.amount == 330000  # 400000 - 70000
    assert result.cash_spent_uncertain is False


@pytest.mark.asyncio
async def test_get_month_summary_cash_spent_uncertain(
    fake_income_repo: IncomeRepository,
    fake_fixed_item_history_repo: FixedItemHistoryRepository,
    fake_card_statement_repo: CardStatementRepository,
    fake_cash_balance_repo: CashBalanceRepository,
    fake_withdrawal_repo: WithdrawalRepository,
    fake_card_repo: CardRepository,
    fake_logger: Logger,
) -> None:
    """次月月初現金が未登録の場合の警告"""
    income = Income.of(
        salary_gross=500000,
        salary_net=400000,
        bonus_gross=0,
        bonus_net=0,
    )
    fake_income_repo.find = AsyncMock(return_value=income)

    # 月初現金のみ設定（次月月初現金は未登録）
    cash_start = CashBalance(
        id=1,
        year_month=YearMonth(2024, 5),
        amount=Money(100000),
    )
    fake_cash_balance_repo.find = AsyncMock(side_effect=[cash_start, None])

    withdrawal = Withdrawal(
        id=1,
        year_month=YearMonth(2024, 5),
        withdrawal_date=date(2024, 5, 15),
        amount=Money(20000),
        note="",
    )
    fake_withdrawal_repo.find_by_year_month = AsyncMock(return_value=[withdrawal])

    usecase = GetMonthSummaryUseCase(
        income_repo=fake_income_repo,
        fixed_item_history_repo=fake_fixed_item_history_repo,
        card_statement_repo=fake_card_statement_repo,
        cash_balance_repo=fake_cash_balance_repo,
        withdrawal_repo=fake_withdrawal_repo,
        card_repo=fake_card_repo,
        logger=fake_logger,
    )

    result = await usecase.execute(2024, 5)

    assert result.cash_spent_uncertain is True
    assert "次月月初現金が未登録のため、現金支出が未確定です。" in result.warnings
    # 表示用の値（月初現金 + 引出）
    assert result.summary.variable_total.amount == 120000  # 100000 + 20000


@pytest.mark.asyncio
async def test_get_month_summary_variable_card_negative(
    fake_income_repo: IncomeRepository,
    fake_fixed_item_history_repo: FixedItemHistoryRepository,
    fake_card_statement_repo: CardStatementRepository,
    fake_cash_balance_repo: CashBalanceRepository,
    fake_withdrawal_repo: WithdrawalRepository,
    fake_card_repo: CardRepository,
    fake_logger: Logger,
) -> None:
    """カード変動費が負値になる場合の警告"""
    income = Income.of(
        salary_gross=500000,
        salary_net=400000,
        bonus_gross=0,
        bonus_net=0,
    )
    fake_income_repo.find = AsyncMock(return_value=income)

    # カードに含まれる固定費を設定
    fixed_history = FixedItemHistory(
        id=1,
        fixed_item_id=1,
        effective_from=YearMonth(2024, 1),
        amount=Money(100000),
        card_id=1,
        included_in_card=True,
    )
    fake_fixed_item_history_repo.find_active_at = AsyncMock(return_value=[fixed_history])

    # カード請求（固定費より少ない）
    card_statement = CardStatement(
        id=1,
        year_month=YearMonth(2024, 5),
        card_id=1,
        amount=Money(50000),  # 固定費100000より少ない
    )
    fake_card_statement_repo.find_by_year_month = AsyncMock(return_value=[card_statement])

    usecase = GetMonthSummaryUseCase(
        income_repo=fake_income_repo,
        fixed_item_history_repo=fake_fixed_item_history_repo,
        card_statement_repo=fake_card_statement_repo,
        cash_balance_repo=fake_cash_balance_repo,
        withdrawal_repo=fake_withdrawal_repo,
        card_repo=fake_card_repo,
        logger=fake_logger,
    )

    result = await usecase.execute(2024, 5)

    assert result.variable_card_negative is True
    assert "カード変動費が負値になっています。固定費の設定を確認してください。" in result.warnings
    # 負の値は0に補正される
    assert result.summary.variable_total.amount == 0


@pytest.mark.asyncio
async def test_get_month_summary_negative_profit(
    fake_income_repo: IncomeRepository,
    fake_fixed_item_history_repo: FixedItemHistoryRepository,
    fake_card_statement_repo: CardStatementRepository,
    fake_cash_balance_repo: CashBalanceRepository,
    fake_withdrawal_repo: WithdrawalRepository,
    fake_card_repo: CardRepository,
    fake_logger: Logger,
) -> None:
    """損益が負の値（赤字）になる場合"""
    income = Income.of(
        salary_gross=500000,
        salary_net=300000,
        bonus_gross=0,
        bonus_net=0,
    )
    fake_income_repo.find = AsyncMock(return_value=income)

    # 固定費と変動費を設定（収入を上回る）
    fixed_history = FixedItemHistory(
        id=1,
        fixed_item_id=1,
        effective_from=YearMonth(2024, 1),
        amount=Money(200000),
        card_id=None,
        included_in_card=False,
    )
    fake_fixed_item_history_repo.find_active_at = AsyncMock(return_value=[fixed_history])

    card_statement = CardStatement(
        id=1,
        year_month=YearMonth(2024, 5),
        card_id=1,
        amount=Money(150000),
    )
    fake_card_statement_repo.find_by_year_month = AsyncMock(return_value=[card_statement])

    usecase = GetMonthSummaryUseCase(
        income_repo=fake_income_repo,
        fixed_item_history_repo=fake_fixed_item_history_repo,
        card_statement_repo=fake_card_statement_repo,
        cash_balance_repo=fake_cash_balance_repo,
        withdrawal_repo=fake_withdrawal_repo,
        card_repo=fake_card_repo,
        logger=fake_logger,
    )

    result = await usecase.execute(2024, 5)

    # 損益 = 300000 - 200000 - 150000 = -50000
    assert result.summary.profit.amount == -50000
    assert result.summary.profit.amount < 0
