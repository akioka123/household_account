"""RegisterCardStatementsUseCaseのテスト"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.port.card_repository import CardRepository
from app.application.port.card_statement_repository import CardStatementRepository
from app.application.port.logger import Logger
from app.application.port.settings_repository import SettingsRepository
from app.application.usecase.register_card_statements import (
    CardStatementCommand,
    RegisterCardStatementsUseCase,
)
from app.domain.model.card_statement import CardStatement
from app.domain.model.money import Money
from app.domain.model.settings import Settings
from app.domain.model.year_month import YearMonth


@pytest.fixture
def fake_card_statement_repo() -> CardStatementRepository:
    """Fake CardStatementRepository"""
    repo = MagicMock(spec=CardStatementRepository)
    repo.find_by_year_month = AsyncMock(return_value=[])
    repo.find_all = AsyncMock(return_value=[])
    repo.save = AsyncMock()
    repo.delete = AsyncMock()
    return repo


@pytest.fixture
def fake_card_repo() -> CardRepository:
    """Fake CardRepository"""
    repo = MagicMock(spec=CardRepository)
    repo.find_by_id = AsyncMock(return_value=None)
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
async def test_register_card_statements_success(
    fake_card_statement_repo: CardStatementRepository,
    fake_card_repo: CardRepository,
    fake_settings_repo: SettingsRepository,
    fake_logger: Logger,
) -> None:
    """カード請求登録が成功する場合"""
    from app.domain.model.card import Card

    # カードが存在することをモック
    card1 = Card(id=1, name="テストカード1", enabled=True)
    card2 = Card(id=2, name="テストカード2", enabled=True)
    fake_card_repo.find_by_id = AsyncMock(side_effect=[card1, card2])
    # find_all()が呼ばれることを確認（ID生成用）
    fake_card_statement_repo.find_all = AsyncMock(return_value=[])

    usecase = RegisterCardStatementsUseCase(
        card_statement_repo=fake_card_statement_repo,
        card_repo=fake_card_repo,
        settings_repo=fake_settings_repo,
        logger=fake_logger,
    )

    commands = [
        CardStatementCommand(card_id=1, amount=50000),
        CardStatementCommand(card_id=2, amount=30000),
    ]

    await usecase.execute(2024, 3, commands)

    # find_all()が呼ばれたことを確認（グローバルなID生成のため）
    fake_card_statement_repo.find_all.assert_called_once()
    # リポジトリのsaveが2回呼ばれたことを確認
    assert fake_card_statement_repo.save.call_count == 2
    # 最初のIDが1、2番目のIDが2になることを確認
    call_args_list = fake_card_statement_repo.save.call_args_list
    assert call_args_list[0][0][0].id == 1
    assert call_args_list[1][0][0].id == 2


@pytest.mark.asyncio
async def test_register_card_statements_with_existing_statements(
    fake_card_statement_repo: CardStatementRepository,
    fake_card_repo: CardRepository,
    fake_settings_repo: SettingsRepository,
    fake_logger: Logger,
) -> None:
    """カード請求登録（既存の請求がある場合、IDがグローバルに一意になることを確認）"""
    from app.domain.model.card import Card

    # カードが存在することをモック
    card = Card(id=1, name="テストカード", enabled=True)
    fake_card_repo.find_by_id = AsyncMock(return_value=card)
    
    # 既存の請求（異なる月の請求を含む）
    existing_statement = CardStatement(
        id=7,
        year_month=YearMonth(2024, 2),  # 異なる月
        card_id=3,  # 異なるカード
        amount=Money(40000),
    )
    fake_card_statement_repo.find_by_year_month = AsyncMock(return_value=[])
    fake_card_statement_repo.find_all = AsyncMock(return_value=[existing_statement])

    usecase = RegisterCardStatementsUseCase(
        card_statement_repo=fake_card_statement_repo,
        card_repo=fake_card_repo,
        settings_repo=fake_settings_repo,
        logger=fake_logger,
    )

    commands = [CardStatementCommand(card_id=1, amount=50000)]

    await usecase.execute(2024, 3, commands)

    # find_all()が呼ばれたことを確認
    fake_card_statement_repo.find_all.assert_called_once()
    fake_card_statement_repo.save.assert_called_once()
    call_args = fake_card_statement_repo.save.call_args[0]
    # 最大ID（7）の次なので、IDは8になる
    assert call_args[0].id == 8


@pytest.mark.asyncio
async def test_register_card_statements_with_invalid_card(
    fake_card_statement_repo: CardStatementRepository,
    fake_card_repo: CardRepository,
    fake_settings_repo: SettingsRepository,
    fake_logger: Logger,
) -> None:
    """無効なカードIDの場合"""
    # カードが見つからないことをモック
    fake_card_repo.find_by_id = AsyncMock(return_value=None)

    usecase = RegisterCardStatementsUseCase(
        card_statement_repo=fake_card_statement_repo,
        card_repo=fake_card_repo,
        settings_repo=fake_settings_repo,
        logger=fake_logger,
    )

    commands = [CardStatementCommand(card_id=999, amount=50000)]

    with pytest.raises(ValueError, match="Card not found"):
        await usecase.execute(2024, 3, commands)


@pytest.mark.asyncio
async def test_register_card_statements_over_limit_raises(
    fake_card_statement_repo: CardStatementRepository,
    fake_card_repo: CardRepository,
    fake_settings_repo: SettingsRepository,
    fake_logger: Logger,
) -> None:
    """UT-RCS-01: 登録件数が上限（max_variable_items）を超える場合はValueError"""
    fake_settings_repo.find = AsyncMock(
        return_value=Settings(max_variable_items=1, max_fixed_items=20)
    )

    usecase = RegisterCardStatementsUseCase(
        card_statement_repo=fake_card_statement_repo,
        card_repo=fake_card_repo,
        settings_repo=fake_settings_repo,
        logger=fake_logger,
    )

    commands = [
        CardStatementCommand(card_id=1, amount=10000),
        CardStatementCommand(card_id=2, amount=20000),
    ]

    with pytest.raises(ValueError, match="上限"):
        await usecase.execute(2024, 3, commands)

    fake_card_statement_repo.save.assert_not_called()

