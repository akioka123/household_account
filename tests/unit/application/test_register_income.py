"""RegisterIncomeUseCaseのテスト"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.port.income_repository import IncomeRepository
from app.application.port.logger import Logger
from app.application.usecase.register_income import (
    RegisterIncomeCommand,
    RegisterIncomeUseCase,
)
from app.domain.model.income import Income
from app.domain.model.year_month import YearMonth


@pytest.fixture
def fake_income_repo() -> IncomeRepository:
    """Fake IncomeRepository"""
    repo = MagicMock(spec=IncomeRepository)
    repo.upsert = AsyncMock()
    return repo


@pytest.fixture
def fake_logger() -> Logger:
    """Fake Logger"""
    logger = MagicMock(spec=Logger)
    logger.info = MagicMock()
    return logger


@pytest.mark.asyncio
async def test_register_income_success(
    fake_income_repo: IncomeRepository,
    fake_logger: Logger,
) -> None:
    """収入登録が成功する場合"""
    usecase = RegisterIncomeUseCase(
        income_repo=fake_income_repo,
        logger=fake_logger,
    )

    command = RegisterIncomeCommand(
        year=2024,
        month=3,
        salary_gross=500000,
        salary_net=400000,
        bonus_gross=1000000,
        bonus_net=800000,
    )

    await usecase.execute(command)

    # リポジトリのupsertが呼ばれたことを確認
    fake_income_repo.upsert.assert_called_once()
    call_args = fake_income_repo.upsert.call_args[0]
    assert isinstance(call_args[0], YearMonth)
    assert call_args[0].year == 2024
    assert call_args[0].month == 3
    assert isinstance(call_args[1], Income)
    assert call_args[1].salary_gross.amount == 500000
    assert call_args[1].salary_net.amount == 400000
    assert call_args[1].bonus_gross.amount == 1000000
    assert call_args[1].bonus_net.amount == 800000


@pytest.mark.asyncio
async def test_register_income_without_bonus(
    fake_income_repo: IncomeRepository,
    fake_logger: Logger,
) -> None:
    """賞与なしで収入登録する場合"""
    usecase = RegisterIncomeUseCase(
        income_repo=fake_income_repo,
        logger=fake_logger,
    )

    command = RegisterIncomeCommand(
        year=2024,
        month=3,
        salary_gross=500000,
        salary_net=400000,
        bonus_gross=0,
        bonus_net=0,
    )

    await usecase.execute(command)

    fake_income_repo.upsert.assert_called_once()
    call_args = fake_income_repo.upsert.call_args[0]
    income = call_args[1]
    assert income.bonus_gross.amount == 0
    assert income.bonus_net.amount == 0
