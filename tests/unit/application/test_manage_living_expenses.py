"""ManageLivingExpensesUseCase tests."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.port.living_expense_repository import LivingExpenseRepository
from app.application.port.logger import Logger
from app.application.usecase.manage_living_expenses import (
    AddLivingExpenseCommand,
    DeleteLivingExpenseCommand,
    ManageLivingExpensesUseCase,
    UpdateLivingExpenseCommand,
)
from app.domain.model.living_expense import (
    LIVING_EXPENSE_CATEGORY_ELECTRICITY,
    LIVING_EXPENSE_CATEGORY_FOOD,
    LivingExpense,
)
from app.domain.model.money import Money
from app.domain.model.year_month import YearMonth


@pytest.fixture
def fake_living_expense_repo() -> LivingExpenseRepository:
    """Fake LivingExpenseRepository."""
    repo = MagicMock(spec=LivingExpenseRepository)
    repo.find_all = AsyncMock(return_value=[])
    repo.find_by_year_month = AsyncMock(return_value=[])
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
async def test_add_living_expense_requires_location_for_food(
    fake_living_expense_repo: LivingExpenseRepository,
    fake_logger: Logger,
) -> None:
    usecase = ManageLivingExpensesUseCase(fake_living_expense_repo, fake_logger)
    command = AddLivingExpenseCommand(
        year=2024,
        month=3,
        category=LIVING_EXPENSE_CATEGORY_FOOD,
        location="",
        amount=1200,
        note="",
    )

    with pytest.raises(ValueError):
        await usecase.add_living_expense(command)

    fake_living_expense_repo.save.assert_not_called()


@pytest.mark.asyncio
async def test_add_living_expense_allows_empty_location_for_non_food(
    fake_living_expense_repo: LivingExpenseRepository,
    fake_logger: Logger,
) -> None:
    usecase = ManageLivingExpensesUseCase(fake_living_expense_repo, fake_logger)
    command = AddLivingExpenseCommand(
        year=2024,
        month=3,
        category=LIVING_EXPENSE_CATEGORY_ELECTRICITY,
        location="",
        amount=8000,
        note="",
    )

    await usecase.add_living_expense(command)

    fake_living_expense_repo.save.assert_called_once()
    saved = fake_living_expense_repo.save.call_args.args[0]
    assert saved.id == 1
    assert saved.category == LIVING_EXPENSE_CATEGORY_ELECTRICITY
    assert saved.location == ""
    assert saved.amount.amount == 8000


@pytest.mark.asyncio
async def test_update_living_expense_saves_existing_id(
    fake_living_expense_repo: LivingExpenseRepository,
    fake_logger: Logger,
) -> None:
    usecase = ManageLivingExpensesUseCase(fake_living_expense_repo, fake_logger)
    command = UpdateLivingExpenseCommand(
        living_expense_id=10,
        year=2024,
        month=3,
        category=LIVING_EXPENSE_CATEGORY_FOOD,
        location="スーパー",
        amount=3000,
        note="夕食",
    )

    await usecase.update_living_expense(command)

    fake_living_expense_repo.save.assert_called_once()
    saved = fake_living_expense_repo.save.call_args.args[0]
    assert saved.id == 10
    assert saved.location == "スーパー"
    assert saved.amount.amount == 3000


@pytest.mark.asyncio
async def test_delete_living_expense_deletes_by_id(
    fake_living_expense_repo: LivingExpenseRepository,
    fake_logger: Logger,
) -> None:
    usecase = ManageLivingExpensesUseCase(fake_living_expense_repo, fake_logger)

    await usecase.delete_living_expense(DeleteLivingExpenseCommand(living_expense_id=10))

    fake_living_expense_repo.delete.assert_called_once_with(10)


@pytest.mark.asyncio
async def test_get_living_expense_data_groups_and_totals_by_category(
    fake_living_expense_repo: LivingExpenseRepository,
    fake_logger: Logger,
) -> None:
    ym = YearMonth(2024, 3)
    food = LivingExpense(
        id=1,
        year_month=ym,
        category=LIVING_EXPENSE_CATEGORY_FOOD,
        location="スーパー",
        amount=Money(1200),
        note="",
    )
    electricity = LivingExpense(
        id=2,
        year_month=ym,
        category=LIVING_EXPENSE_CATEGORY_ELECTRICITY,
        location="",
        amount=Money(8000),
        note="",
    )
    fake_living_expense_repo.find_by_year_month = AsyncMock(return_value=[food, electricity])
    usecase = ManageLivingExpensesUseCase(fake_living_expense_repo, fake_logger)

    result = await usecase.get_living_expense_data(2024, 3)

    assert result.by_category[LIVING_EXPENSE_CATEGORY_FOOD] == [food]
    assert result.by_category[LIVING_EXPENSE_CATEGORY_ELECTRICITY] == [electricity]
    assert result.totals_by_category[LIVING_EXPENSE_CATEGORY_FOOD].amount == 1200
    assert result.totals_by_category[LIVING_EXPENSE_CATEGORY_ELECTRICITY].amount == 8000
