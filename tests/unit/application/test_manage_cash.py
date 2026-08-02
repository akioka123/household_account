"""ManageCashUseCase tests."""
from __future__ import annotations

from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.port.cash_balance_repository import CashBalanceRepository
from app.application.port.logger import Logger
from app.application.port.withdrawal_repository import WithdrawalRepository
from app.application.usecase.manage_cash import (
    AddWithdrawalCommand,
    DeleteWithdrawalCommand,
    ManageCashUseCase,
    UpdateCashBalanceCommand,
)
from app.domain.model.cash_balance import CashBalance
from app.domain.model.money import Money
from app.domain.model.withdrawal import Withdrawal
from app.domain.model.year_month import YearMonth


@pytest.fixture
def fake_cash_balance_repo() -> CashBalanceRepository:
    """Fake CashBalanceRepository."""
    repo = MagicMock(spec=CashBalanceRepository)
    repo.find = AsyncMock(return_value=None)
    repo.find_all = AsyncMock(return_value=[])
    repo.save = AsyncMock()
    return repo


@pytest.fixture
def fake_withdrawal_repo() -> WithdrawalRepository:
    """Fake WithdrawalRepository."""
    repo = MagicMock(spec=WithdrawalRepository)
    repo.find_by_year_month = AsyncMock(return_value=[])
    repo.find_all = AsyncMock(return_value=[])
    repo.save = AsyncMock()
    repo.delete = AsyncMock()
    return repo


@pytest.fixture
def fake_logger() -> Logger:
    """Fake Logger."""
    logger = MagicMock(spec=Logger)
    logger.info = MagicMock()
    return logger


@pytest.mark.asyncio
async def test_update_cash_balance_new(
    fake_cash_balance_repo: CashBalanceRepository,
    fake_withdrawal_repo: WithdrawalRepository,
    fake_logger: Logger,
) -> None:
    usecase = ManageCashUseCase(
        cash_balance_repo=fake_cash_balance_repo,
        withdrawal_repo=fake_withdrawal_repo,
        logger=fake_logger,
    )

    command = UpdateCashBalanceCommand(year=2024, month=3, amount=100000)
    await usecase.update_cash_balance(command)

    fake_cash_balance_repo.find.assert_called_once_with(YearMonth(2024, 3))
    fake_cash_balance_repo.find_all.assert_called_once()
    fake_cash_balance_repo.save.assert_called_once()
    saved = fake_cash_balance_repo.save.call_args.args[0]
    assert isinstance(saved, CashBalance)
    assert saved.id == 1
    assert saved.amount.amount == 100000


@pytest.mark.asyncio
async def test_update_cash_balance_existing(
    fake_cash_balance_repo: CashBalanceRepository,
    fake_withdrawal_repo: WithdrawalRepository,
    fake_logger: Logger,
) -> None:
    ym = YearMonth(2024, 3)
    existing = CashBalance(id=7, year_month=ym, amount=Money(50000))
    fake_cash_balance_repo.find = AsyncMock(return_value=existing)
    usecase = ManageCashUseCase(
        cash_balance_repo=fake_cash_balance_repo,
        withdrawal_repo=fake_withdrawal_repo,
        logger=fake_logger,
    )

    command = UpdateCashBalanceCommand(year=2024, month=3, amount=150000)
    await usecase.update_cash_balance(command)

    fake_cash_balance_repo.find_all.assert_not_called()
    fake_cash_balance_repo.save.assert_called_once()
    saved = fake_cash_balance_repo.save.call_args.args[0]
    assert saved.id == 7
    assert saved.amount.amount == 150000


@pytest.mark.asyncio
async def test_add_withdrawal(
    fake_cash_balance_repo: CashBalanceRepository,
    fake_withdrawal_repo: WithdrawalRepository,
    fake_logger: Logger,
) -> None:
    usecase = ManageCashUseCase(
        cash_balance_repo=fake_cash_balance_repo,
        withdrawal_repo=fake_withdrawal_repo,
        logger=fake_logger,
    )

    command = AddWithdrawalCommand(
        year=2024,
        month=3,
        withdrawal_date=date(2024, 3, 15),
        amount=50000,
        note="買い物",
    )
    await usecase.add_withdrawal(command)

    fake_withdrawal_repo.find_all.assert_called_once()
    fake_withdrawal_repo.save.assert_called_once()
    saved = fake_withdrawal_repo.save.call_args.args[0]
    assert isinstance(saved, Withdrawal)
    assert saved.id == 1
    assert saved.withdrawal_date == date(2024, 3, 15)
    assert saved.amount.amount == 50000
    assert saved.note == "買い物"


@pytest.mark.asyncio
async def test_add_withdrawal_with_existing_withdrawals(
    fake_cash_balance_repo: CashBalanceRepository,
    fake_withdrawal_repo: WithdrawalRepository,
    fake_logger: Logger,
) -> None:
    existing_withdrawal = Withdrawal(
        id=12,
        year_month=YearMonth(2024, 2),
        withdrawal_date=date(2024, 2, 10),
        amount=Money(30000),
        note="既存",
    )
    fake_withdrawal_repo.find_all = AsyncMock(return_value=[existing_withdrawal])
    usecase = ManageCashUseCase(
        cash_balance_repo=fake_cash_balance_repo,
        withdrawal_repo=fake_withdrawal_repo,
        logger=fake_logger,
    )

    command = AddWithdrawalCommand(
        year=2024,
        month=3,
        withdrawal_date=date(2024, 3, 15),
        amount=50000,
        note="買い物",
    )
    await usecase.add_withdrawal(command)

    saved = fake_withdrawal_repo.save.call_args.args[0]
    assert saved.id == 13


@pytest.mark.asyncio
async def test_delete_withdrawal(
    fake_cash_balance_repo: CashBalanceRepository,
    fake_withdrawal_repo: WithdrawalRepository,
    fake_logger: Logger,
) -> None:
    usecase = ManageCashUseCase(
        cash_balance_repo=fake_cash_balance_repo,
        withdrawal_repo=fake_withdrawal_repo,
        logger=fake_logger,
    )

    await usecase.delete_withdrawal(DeleteWithdrawalCommand(withdrawal_id=13))

    fake_withdrawal_repo.delete.assert_called_once_with(13)


@pytest.mark.asyncio
async def test_get_cash_data(
    fake_cash_balance_repo: CashBalanceRepository,
    fake_withdrawal_repo: WithdrawalRepository,
    fake_logger: Logger,
) -> None:
    ym = YearMonth(2024, 3)
    next_ym = YearMonth(2024, 4)
    balance = CashBalance(id=1, year_month=ym, amount=Money(100000))
    next_balance = CashBalance(id=2, year_month=next_ym, amount=Money(50000))
    withdrawals = [
        Withdrawal(
            id=1,
            year_month=ym,
            withdrawal_date=date(2024, 3, 15),
            amount=Money(50000),
            note="買い物",
        ),
        Withdrawal(
            id=2,
            year_month=ym,
            withdrawal_date=date(2024, 3, 20),
            amount=Money(30000),
            note="食事",
        ),
    ]
    fake_cash_balance_repo.find = AsyncMock(
        side_effect=lambda requested_ym: balance if requested_ym == ym else next_balance
    )
    fake_withdrawal_repo.find_by_year_month = AsyncMock(return_value=withdrawals)
    usecase = ManageCashUseCase(
        cash_balance_repo=fake_cash_balance_repo,
        withdrawal_repo=fake_withdrawal_repo,
        logger=fake_logger,
    )

    result = await usecase.get_cash_data(2024, 3)

    assert result.cash_start == balance
    assert result.cash_start_next == next_balance
    assert result.withdrawals == withdrawals
