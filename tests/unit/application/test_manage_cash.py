"""ManageCashUseCaseのテスト"""
from __future__ import annotations

from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.port.cash_balance_repository import CashBalanceRepository
from app.application.port.logger import Logger
from app.application.port.withdrawal_repository import WithdrawalRepository
from app.application.usecase.manage_cash import (
    DeleteWithdrawalCommand,
    ManageCashUseCase,
    SaveCashBalanceCommand,
    SaveWithdrawalCommand,
)
from app.domain.model.cash_balance import CashBalance
from app.domain.model.money import Money
from app.domain.model.withdrawal import Withdrawal
from app.domain.model.year_month import YearMonth


@pytest.fixture
def fake_cash_balance_repo() -> CashBalanceRepository:
    """Fake CashBalanceRepository"""
    repo = MagicMock(spec=CashBalanceRepository)
    repo.find = AsyncMock(return_value=None)
    repo.find_all = AsyncMock(return_value=[])
    repo.save = AsyncMock()
    return repo


@pytest.fixture
def fake_withdrawal_repo() -> WithdrawalRepository:
    """Fake WithdrawalRepository"""
    repo = MagicMock(spec=WithdrawalRepository)
    repo.find_by_year_month = AsyncMock(return_value=[])
    repo.find_all = AsyncMock(return_value=[])
    repo.save = AsyncMock()
    repo.delete = AsyncMock()
    return repo


@pytest.fixture
def fake_logger() -> Logger:
    """Fake Logger"""
    logger = MagicMock(spec=Logger)
    logger.info = MagicMock()
    return logger


@pytest.mark.asyncio
async def test_save_cash_balance_new(
    fake_cash_balance_repo: CashBalanceRepository,
    fake_withdrawal_repo: WithdrawalRepository,
    fake_logger: Logger,
) -> None:
    """現金残高を新規作成"""
    # find_all()が呼ばれることを確認（ID生成用）
    fake_cash_balance_repo.find_all = AsyncMock(return_value=[])
    
    usecase = ManageCashUseCase(
        cash_balance_repo=fake_cash_balance_repo,
        withdrawal_repo=fake_withdrawal_repo,
        logger=fake_logger,
    )

    command = SaveCashBalanceCommand(year=2024, month=3, amount=100000)
    await usecase.save_cash_balance(command)

    # find_all()が呼ばれたことを確認（グローバルなID生成のため）
    fake_cash_balance_repo.find_all.assert_called_once()
    fake_cash_balance_repo.save.assert_called_once()
    call_args = fake_cash_balance_repo.save.call_args[0]
    assert isinstance(call_args[0], CashBalance)
    assert call_args[0].amount.amount == 100000
    assert call_args[0].id == 1  # 最初の残高なのでIDは1


@pytest.mark.asyncio
async def test_save_cash_balance_update(
    fake_cash_balance_repo: CashBalanceRepository,
    fake_withdrawal_repo: WithdrawalRepository,
    fake_logger: Logger,
) -> None:
    """現金残高を更新"""
    ym = YearMonth(2024, 3)
    existing = CashBalance(id=1, year_month=ym, amount=Money(50000))
    fake_cash_balance_repo.find = AsyncMock(return_value=existing)

    usecase = ManageCashUseCase(
        cash_balance_repo=fake_cash_balance_repo,
        withdrawal_repo=fake_withdrawal_repo,
        logger=fake_logger,
    )

    command = SaveCashBalanceCommand(year=2024, month=3, amount=150000)
    await usecase.save_cash_balance(command)

    fake_cash_balance_repo.save.assert_called_once()
    call_args = fake_cash_balance_repo.save.call_args[0]
    assert call_args[0].id == 1
    assert call_args[0].amount.amount == 150000


@pytest.mark.asyncio
async def test_save_withdrawal(
    fake_cash_balance_repo: CashBalanceRepository,
    fake_withdrawal_repo: WithdrawalRepository,
    fake_logger: Logger,
) -> None:
    """引出明細を保存"""
    # find_all()が呼ばれることを確認（ID生成用）
    fake_withdrawal_repo.find_all = AsyncMock(return_value=[])
    
    usecase = ManageCashUseCase(
        cash_balance_repo=fake_cash_balance_repo,
        withdrawal_repo=fake_withdrawal_repo,
        logger=fake_logger,
    )

    command = SaveWithdrawalCommand(
        year=2024, month=3, date=15, amount=50000, note="買い物"
    )
    await usecase.save_withdrawal(command)

    # find_all()が呼ばれたことを確認（グローバルなID生成のため）
    fake_withdrawal_repo.find_all.assert_called_once()
    fake_withdrawal_repo.save.assert_called_once()
    call_args = fake_withdrawal_repo.save.call_args[0]
    assert isinstance(call_args[0], Withdrawal)
    assert call_args[0].date == 15
    assert call_args[0].amount.amount == 50000
    assert call_args[0].note == "買い物"
    assert call_args[0].id == 1  # 最初の引出なのでIDは1


@pytest.mark.asyncio
async def test_save_withdrawal_with_existing_withdrawals(
    fake_cash_balance_repo: CashBalanceRepository,
    fake_withdrawal_repo: WithdrawalRepository,
    fake_logger: Logger,
) -> None:
    """引出明細を保存（既存の引出がある場合、IDがグローバルに一意になることを確認）"""
    # 既存の引出（異なる月の引出を含む）
    existing_withdrawal = Withdrawal(
        id=12,
        year_month=YearMonth(2024, 2),  # 異なる月
        withdrawal_date=date(2024, 2, 10),
        amount=Money(30000),
        note="既存の引出",
    )
    fake_withdrawal_repo.find_all = AsyncMock(return_value=[existing_withdrawal])
    
    usecase = ManageCashUseCase(
        cash_balance_repo=fake_cash_balance_repo,
        withdrawal_repo=fake_withdrawal_repo,
        logger=fake_logger,
    )

    command = SaveWithdrawalCommand(
        year=2024, month=3, date=15, amount=50000, note="買い物"
    )
    await usecase.save_withdrawal(command)

    # find_all()が呼ばれたことを確認
    fake_withdrawal_repo.find_all.assert_called_once()
    fake_withdrawal_repo.save.assert_called_once()
    call_args = fake_withdrawal_repo.save.call_args[0]
    # 最大ID（12）の次なので、IDは13になる
    assert call_args[0].id == 13


@pytest.mark.asyncio
async def test_get_cash_data(
    fake_cash_balance_repo: CashBalanceRepository,
    fake_withdrawal_repo: WithdrawalRepository,
    fake_logger: Logger,
) -> None:
    """現金データを取得"""
    ym = YearMonth(2024, 3)
    balance = CashBalance(id=1, year_month=ym, amount=Money(100000))
    withdrawal1 = Withdrawal(
        id=1, year_month=ym, date=15, amount=Money(50000), note="買い物"
    )
    withdrawal2 = Withdrawal(
        id=2, year_month=ym, date=20, amount=Money(30000), note="食事"
    )

    fake_cash_balance_repo.find = AsyncMock(return_value=balance)
    fake_withdrawal_repo.find_by_year_month = AsyncMock(
        return_value=[withdrawal1, withdrawal2]
    )

    usecase = ManageCashUseCase(
        cash_balance_repo=fake_cash_balance_repo,
        withdrawal_repo=fake_withdrawal_repo,
        logger=fake_logger,
    )

    result_balance, result_withdrawals = await usecase.get_cash_data(2024, 3)

    assert result_balance == balance
    assert len(result_withdrawals) == 2
    assert result_withdrawals[0].id == 1
    assert result_withdrawals[1].id == 2
