"""RegisterCardStatementsUseCaseのテスト"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.port.card_repository import CardRepository
from app.application.port.card_statement_repository import CardStatementRepository
from app.application.port.logger import Logger
from app.application.usecase.register_card_statements import (
    CardStatementCommand,
    RegisterCardStatementsUseCase,
)
from app.domain.model.card_statement import CardStatement
from app.domain.model.money import Money
from app.domain.model.year_month import YearMonth


@pytest.fixture
def fake_card_statement_repo() -> CardStatementRepository:
    """Fake CardStatementRepository"""
    repo = MagicMock(spec=CardStatementRepository)
    repo.find_by_year_month = AsyncMock(return_value=[])
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


@pytest.mark.asyncio
async def test_register_card_statements_success(
    fake_card_statement_repo: CardStatementRepository,
    fake_card_repo: CardRepository,
    fake_logger: Logger,
) -> None:
    """カード請求登録が成功する場合"""
    from app.domain.model.card import Card

    # カードが存在することをモック
    card = Card(id=1, name="テストカード", enabled=True)
    fake_card_repo.find_by_id = AsyncMock(return_value=card)

    usecase = RegisterCardStatementsUseCase(
        card_statement_repo=fake_card_statement_repo,
        card_repo=fake_card_repo,
        logger=fake_logger,
    )

    commands = [
        CardStatementCommand(card_id=1, amount=50000),
        CardStatementCommand(card_id=2, amount=30000),
    ]

    await usecase.execute(2024, 3, commands)

    # リポジトリのsaveが2回呼ばれたことを確認
    assert fake_card_statement_repo.save.call_count == 2


@pytest.mark.asyncio
async def test_register_card_statements_with_invalid_card(
    fake_card_statement_repo: CardStatementRepository,
    fake_card_repo: CardRepository,
    fake_logger: Logger,
) -> None:
    """無効なカードIDの場合"""
    # カードが見つからないことをモック
    fake_card_repo.find_by_id = AsyncMock(return_value=None)

    usecase = RegisterCardStatementsUseCase(
        card_statement_repo=fake_card_statement_repo,
        card_repo=fake_card_repo,
        logger=fake_logger,
    )

    commands = [CardStatementCommand(card_id=999, amount=50000)]

    with pytest.raises(ValueError, match="Card not found"):
        await usecase.execute(2024, 3, commands)
