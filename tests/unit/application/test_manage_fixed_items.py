"""ManageFixedItemsUseCaseのテスト"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.port.fixed_item_history_repository import FixedItemHistoryRepository
from app.application.port.fixed_item_repository import FixedItemRepository
from app.application.port.logger import Logger
from app.application.port.settings_repository import SettingsRepository
from app.application.usecase.manage_fixed_items import (
    AddFixedItemCommand,
    AddFixedItemHistoryCommand,
    EndFixedItemOperationCommand,
    ManageFixedItemsUseCase,
)
from app.domain.model.fixed_item import FixedItem
from app.domain.model.fixed_item_history import FixedItemHistory
from app.domain.model.money import Money
from app.domain.model.settings import Settings
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
    repo.find_all = AsyncMock(return_value=[])
    repo.find_active_at = AsyncMock(return_value=[])
    repo.save = AsyncMock()
    return repo


@pytest.fixture
def fake_logger() -> Logger:
    """Fake Logger"""
    logger = MagicMock(spec=Logger)
    logger.info = MagicMock()
    return logger


@pytest.fixture
def fake_settings_repo() -> SettingsRepository:
    """Fake SettingsRepository（上限20件のデフォルト設定を返す）"""
    repo = MagicMock(spec=SettingsRepository)
    repo.find = AsyncMock(return_value=Settings.default())
    return repo


@pytest.mark.asyncio
async def test_add_fixed_item(
    fake_fixed_item_repo: FixedItemRepository,
    fake_settings_repo: SettingsRepository,
    fake_logger: Logger,
) -> None:
    """固定費項目を追加"""
    usecase = ManageFixedItemsUseCase(
        fixed_item_repo=fake_fixed_item_repo,
        fixed_item_history_repo=MagicMock(),
        settings_repo=fake_settings_repo,
        logger=fake_logger,
    )

    command = AddFixedItemCommand(name="家賃")
    await usecase.add_fixed_item(command)

    fake_fixed_item_repo.save.assert_called_once()
    call_args = fake_fixed_item_repo.save.call_args[0]
    assert isinstance(call_args[0], FixedItem)
    assert call_args[0].name == "家賃"


@pytest.mark.asyncio
async def test_add_fixed_item_over_limit_raises(
    fake_fixed_item_repo: FixedItemRepository,
    fake_settings_repo: SettingsRepository,
    fake_logger: Logger,
) -> None:
    """UT-MFI-01: 固定費項目数が上限（max_fixed_items）に達している場合はValueError"""
    fake_fixed_item_repo.find_all = AsyncMock(return_value=[FixedItem(id=1, name="家賃")])
    fake_settings_repo.find = AsyncMock(
        return_value=Settings(max_variable_items=20, max_fixed_items=1)
    )

    usecase = ManageFixedItemsUseCase(
        fixed_item_repo=fake_fixed_item_repo,
        fixed_item_history_repo=MagicMock(),
        settings_repo=fake_settings_repo,
        logger=fake_logger,
    )

    with pytest.raises(ValueError, match="上限"):
        await usecase.add_fixed_item(AddFixedItemCommand(name="光熱費"))

    fake_fixed_item_repo.save.assert_not_called()


@pytest.mark.asyncio
async def test_add_fixed_item_history(
    fake_fixed_item_repo: FixedItemRepository,
    fake_fixed_item_history_repo: FixedItemHistoryRepository,
    fake_settings_repo: SettingsRepository,
    fake_logger: Logger,
) -> None:
    """固定費履歴を追加"""
    # 固定費項目が存在することをモック
    fixed_item = FixedItem(id=1, name="家賃")
    fake_fixed_item_repo.find_by_id = AsyncMock(return_value=fixed_item)
    # find_all()が呼ばれることを確認（ID生成用）
    fake_fixed_item_history_repo.find_all = AsyncMock(return_value=[])

    usecase = ManageFixedItemsUseCase(
        fixed_item_repo=fake_fixed_item_repo,
        fixed_item_history_repo=fake_fixed_item_history_repo,
        settings_repo=fake_settings_repo,
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

    # find_all()が呼ばれたことを確認（グローバルなID生成のため）
    fake_fixed_item_history_repo.find_all.assert_called_once()
    fake_fixed_item_history_repo.save.assert_called_once()
    call_args = fake_fixed_item_history_repo.save.call_args[0]
    assert isinstance(call_args[0], FixedItemHistory)
    assert call_args[0].fixed_item_id == 1
    assert call_args[0].amount.amount == 100000
    assert call_args[0].id == 1  # 最初の履歴なのでIDは1


@pytest.mark.asyncio
async def test_add_fixed_item_history_with_existing_histories(
    fake_fixed_item_repo: FixedItemRepository,
    fake_fixed_item_history_repo: FixedItemHistoryRepository,
    fake_settings_repo: SettingsRepository,
    fake_logger: Logger,
) -> None:
    """固定費履歴を追加（既存の履歴がある場合、IDがグローバルに一意になることを確認）"""
    # 固定費項目が存在することをモック
    fixed_item = FixedItem(id=1, name="家賃")
    fake_fixed_item_repo.find_by_id = AsyncMock(return_value=fixed_item)
    
    # 既存の履歴（異なる固定費項目の履歴を含む）
    existing_history1 = FixedItemHistory(
        id=5,
        fixed_item_id=2,  # 異なる固定費項目
        effective_from=YearMonth(2024, 1),
        amount=Money(50000),
        card_id=None,
        included_in_card=False,
    )
    existing_history2 = FixedItemHistory(
        id=10,
        fixed_item_id=3,  # 異なる固定費項目
        effective_from=YearMonth(2024, 2),
        amount=Money(30000),
        card_id=None,
        included_in_card=False,
    )
    fake_fixed_item_history_repo.find_all = AsyncMock(
        return_value=[existing_history1, existing_history2]
    )

    usecase = ManageFixedItemsUseCase(
        fixed_item_repo=fake_fixed_item_repo,
        fixed_item_history_repo=fake_fixed_item_history_repo,
        settings_repo=fake_settings_repo,
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

    # find_all()が呼ばれたことを確認
    fake_fixed_item_history_repo.find_all.assert_called_once()
    fake_fixed_item_history_repo.save.assert_called_once()
    call_args = fake_fixed_item_history_repo.save.call_args[0]
    # 最大ID（10）の次なので、IDは11になる
    assert call_args[0].id == 11


@pytest.mark.asyncio
async def test_get_active_fixed_items_at(
    fake_fixed_item_repo: FixedItemRepository,
    fake_fixed_item_history_repo: FixedItemHistoryRepository,
    fake_settings_repo: SettingsRepository,
    fake_logger: Logger,
) -> None:
    """指定年月で有効な固定費を取得"""
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
        settings_repo=fake_settings_repo,
        logger=fake_logger,
    )

    result = await usecase.get_active_fixed_items_at(2024, 3)

    assert len(result) == 2
    assert result[0].fixed_item_id == 1
    assert result[0].amount.amount == 100000
    assert result[1].fixed_item_id == 2
    assert result[1].amount.amount == 50000


@pytest.mark.asyncio
async def test_get_histories_by_fixed_item(
    fake_fixed_item_repo: FixedItemRepository,
    fake_fixed_item_history_repo: FixedItemHistoryRepository,
    fake_settings_repo: SettingsRepository,
    fake_logger: Logger,
) -> None:
    """固定費項目ごとの履歴一覧を取得"""
    item1 = FixedItem(id=1, name="家賃")
    item2 = FixedItem(id=2, name="保険")
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
        amount=Money(5000),
        card_id=1,
        included_in_card=True,
    )
    fake_fixed_item_history_repo.find_by_fixed_item_id = AsyncMock(
        side_effect=[[history1], [history2]]
    )
    usecase = ManageFixedItemsUseCase(
        fixed_item_repo=fake_fixed_item_repo,
        fixed_item_history_repo=fake_fixed_item_history_repo,
        settings_repo=fake_settings_repo,
        logger=fake_logger,
    )

    result = await usecase.get_histories_by_fixed_item([item1, item2])

    assert result == {1: [history1], 2: [history2]}
    assert fake_fixed_item_history_repo.find_by_fixed_item_id.await_count == 2


@pytest.mark.asyncio
async def test_end_fixed_item_operation_adds_zero_amount_history(
    fake_fixed_item_repo: FixedItemRepository,
    fake_fixed_item_history_repo: FixedItemHistoryRepository,
    fake_settings_repo: SettingsRepository,
    fake_logger: Logger,
) -> None:
    """固定費の運用終了履歴を追加"""
    fixed_item = FixedItem(id=1, name="家賃")
    fake_fixed_item_repo.find_by_id = AsyncMock(return_value=fixed_item)
    fake_fixed_item_history_repo.find_all = AsyncMock(return_value=[])
    usecase = ManageFixedItemsUseCase(
        fixed_item_repo=fake_fixed_item_repo,
        fixed_item_history_repo=fake_fixed_item_history_repo,
        settings_repo=fake_settings_repo,
        logger=fake_logger,
    )

    await usecase.end_fixed_item_operation(
        EndFixedItemOperationCommand(fixed_item_id=1, year=2026, month=6)
    )

    fake_fixed_item_history_repo.save.assert_called_once()
    saved = fake_fixed_item_history_repo.save.call_args.args[0]
    assert saved.fixed_item_id == 1
    assert saved.effective_from == YearMonth(2026, 6)
    assert saved.amount.amount == 0
    assert saved.card_id is None
    assert saved.included_in_card is False
    assert saved.is_deleted()

