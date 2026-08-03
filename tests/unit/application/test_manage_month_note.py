"""ManageMonthNoteUseCaseのテスト"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.port.logger import Logger
from app.application.port.month_note_repository import MonthNoteRepository
from app.application.usecase.manage_month_note import (
    ManageMonthNoteUseCase,
    SaveMonthNoteCommand,
)
from app.domain.model.month_note import MONTH_NOTE_MAX_LENGTH, MonthNote
from app.domain.model.year_month import YearMonth


@pytest.fixture
def fake_month_note_repo() -> MonthNoteRepository:
    """Fake MonthNoteRepository"""
    repo = MagicMock(spec=MonthNoteRepository)
    repo.find = AsyncMock(return_value=None)
    repo.find_by_year = AsyncMock(return_value={})
    repo.save = AsyncMock(return_value=None)
    repo.delete = AsyncMock(return_value=None)
    return repo


@pytest.fixture
def fake_logger() -> Logger:
    """Fake Logger"""
    logger = MagicMock(spec=Logger)
    logger.info = MagicMock()
    return logger


@pytest.mark.asyncio
async def test_save_note(
    fake_month_note_repo: MonthNoteRepository,
    fake_logger: Logger,
) -> None:
    """メモを保存する"""
    ym = YearMonth(2024, 5)
    saved = MonthNote(id=1, year_month=ym, note="帰省で交通費が増えた")
    fake_month_note_repo.find = AsyncMock(return_value=saved)

    usecase = ManageMonthNoteUseCase(
        month_note_repo=fake_month_note_repo,
        logger=fake_logger,
    )

    result = await usecase.save_note(
        SaveMonthNoteCommand(year=2024, month=5, note="帰省で交通費が増えた")
    )

    assert result == saved
    fake_month_note_repo.save.assert_awaited_once()
    fake_month_note_repo.delete.assert_not_awaited()


@pytest.mark.asyncio
async def test_save_note_empty_deletes(
    fake_month_note_repo: MonthNoteRepository,
    fake_logger: Logger,
) -> None:
    """空文字で保存するとメモを削除する"""
    usecase = ManageMonthNoteUseCase(
        month_note_repo=fake_month_note_repo,
        logger=fake_logger,
    )

    result = await usecase.save_note(SaveMonthNoteCommand(year=2024, month=5, note="   "))

    assert result is None
    fake_month_note_repo.delete.assert_awaited_once_with(YearMonth(2024, 5))
    fake_month_note_repo.save.assert_not_awaited()


@pytest.mark.asyncio
async def test_save_note_too_long(
    fake_month_note_repo: MonthNoteRepository,
    fake_logger: Logger,
) -> None:
    """最大文字数を超える場合は例外を送出し保存しない"""
    usecase = ManageMonthNoteUseCase(
        month_note_repo=fake_month_note_repo,
        logger=fake_logger,
    )

    with pytest.raises(ValueError):
        await usecase.save_note(
            SaveMonthNoteCommand(year=2024, month=5, note="あ" * (MONTH_NOTE_MAX_LENGTH + 1))
        )

    fake_month_note_repo.save.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_note(
    fake_month_note_repo: MonthNoteRepository,
    fake_logger: Logger,
) -> None:
    """指定年月のメモを取得する"""
    ym = YearMonth(2024, 5)
    note = MonthNote(id=1, year_month=ym, note="特別な出費はなし")
    fake_month_note_repo.find = AsyncMock(return_value=note)

    usecase = ManageMonthNoteUseCase(
        month_note_repo=fake_month_note_repo,
        logger=fake_logger,
    )

    result = await usecase.get_note(2024, 5)

    assert result == note
    fake_month_note_repo.find.assert_awaited_once_with(ym)
