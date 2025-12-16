"""ManageFixedItemsUseCaseのテスト"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.port.fixed_item_history_repository import FixedItemHistoryRepository
from app.application.port.fixed_item_repository import FixedItemRepository
from app.application.port.logger import Logger
from app.application.usecase.manage_fixed_items import (
    AddFixedItemCommand,
    AddFixedItemHistoryCommand,
    ManageFixedItemsUseCase,
)
from app.domain.model.fixed_item import FixedItem
from app.domain.model.fixed_item_history import FixedItemHistory
from app.domain.model.money import Money
from app.domain.model.year_month import YearMonth


@pytest.fixture
def fake_fixed_item_repo() -> FixedItemRepository:
    """Fake FixedItemRepository"""
    repo = MagicMock(spec=FixedItemRepository)
    repo.find_all = AsyncMock(return_value=[])
    repo.find_by_id = AsyncMock(return_value=None)
    repo.save = AsyncMock()
    return repo


@pytest.fixture
def fake_fixed_item_history_repo() -> FixedItemHistoryRepository:
    """Fake FixedItemHistoryRepository"""
    repo = MagicMock(spec=FixedItemHistoryRepository)
    repo.find_by_fixed_item_id = AsyncMock(return_value=[])
    repo.find_active_at = AsyncMock(return_value=[])
    repo.save = AsyncMock()
    return repo


@pytest.fixture
def fake_logger() -> Logger:
    """Fake Logger"""
    logger = MagicMock(spec=Logger)
    logger.info = MagicMock()
    return logger


@pytest.mark.asyncio
async def test_add_fixed_item(
    fake_fixed_item_repo: FixedItemRepository,
    fake_logger: Logger,
) -> None:
    """固定費項目を追加"""
    usecase = ManageFixedItemsUseCase(
        fixed_item_repo=fake_fixed_item_repo,
        fixed_item_history_repo=MagicMock(),
        logger=fake_logger,
    )

    command = AddFixedItemCommand(name="家賃")
    result = await usecase.add_fixed_item(command)

    fake_fixed_item_repo.save.assert_called_once()
    call_args = fake_fixed_item_repo.save.call_args[0]
    assert isinstance(call_args[0], FixedItem)
    assert call_args[0].name == "家賃"


@pytest.mark.asyncio
async def test_add_fixed_item_history(
    fake_fixed_item_repo: FixedItemRepository,
    fake_fixed_item_history_repo: FixedItemHistoryRepository,
    fake_logger: Logger,
) -> None:
    """固定費履歴を追加"""
    # 固定費項目が存在することをモック
    fixed_item = FixedItem(id=1, name="家賃")
    fake_fixed_item_repo.find_by_id = AsyncMock(return_value=fixed_item)

    usecase = ManageFixedItemsUseCase(
        fixed_item_repo=fake_fixed_item_repo,
        fixed_item_history_repo=fake_fixed_item_history_repo,
        logger=fake_logger,
    )

    command = AddFixedItemHistoryCommand(
        fixed_item_id=1,
        year=2024,
        month=3,
        amount=100000,
        card_id=None,
        included_in_card=False,
    )
    await usecase.add_fixed_item_history(command)

    fake_fixed_item_history_repo.save.assert_called_once()
    call_args = fake_fixed_item_history_repo.save.call_args[0]
    assert isinstance(call_args[0], FixedItemHistory)
    assert call_args[0].fixed_item_id == 1
    assert call_args[0].amount.amount == 100000


@pytest.mark.asyncio
async def test_get_active_fixed_items_at(
    fake_fixed_item_repo: FixedItemRepository,
    fake_fixed_item_history_repo: FixedItemHistoryRepository,
    fake_logger: Logger,
) -> None:
    """指定年月で有効な固定費を取得"""
    ym = YearMonth(2024, 3)
    history1 = FixedItemHistory(
        id=1,
        fixed_item_id=1,
        effective_from=YearMonth(2024, 1),
        amount=Money(100000),
        card_id=None,
        included_in_card=False,
    )
    history2 = FixedItemHistory(
        id=2,
        fixed_item_id=2,
        effective_from=YearMonth(2024, 2),
        amount=Money(50000),
        card_id=1,
        included_in_card=True,
    )
    fake_fixed_item_history_repo.find_active_at = AsyncMock(
        return_value=[history1, history2]
    )

    fixed_item1 = FixedItem(id=1, name="家賃")
    fixed_item2 = FixedItem(id=2, name="光熱費")
    fake_fixed_item_repo.find_by_id = AsyncMock(side_effect=[fixed_item1, fixed_item2])

    usecase = ManageFixedItemsUseCase(
        fixed_item_repo=fake_fixed_item_repo,
        fixed_item_history_repo=fake_fixed_item_history_repo,
        logger=fake_logger,
    )

    result = await usecase.get_active_fixed_items_at(2024, 3)

    assert len(result) == 2
    assert result[0].fixed_item_id == 1
    assert result[0].amount.amount == 100000
    assert result[1].fixed_item_id == 2
    assert result[1].amount.amount == 50000

