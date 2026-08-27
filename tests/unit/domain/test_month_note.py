"""MonthNoteのテスト"""
from __future__ import annotations

import pytest

from app.domain.model.month_note import MONTH_NOTE_MAX_LENGTH, MonthNote
from app.domain.model.year_month import YearMonth


def test_month_note_of_strips_whitespace() -> None:
    """前後の空白を除去して作成"""
    note = MonthNote.of(YearMonth(2024, 5), "  帰省の交通費で平均より支出が多かった  ")

    assert note.id == 0
    assert note.year_month == YearMonth(2024, 5)
    assert note.note == "帰省の交通費で平均より支出が多かった"
    assert note.is_empty() is False


def test_month_note_of_empty() -> None:
    """空白のみの場合は空メモとして扱う"""
    note = MonthNote.of(YearMonth(2024, 5), "   ")

    assert note.note == ""
    assert note.is_empty() is True


def test_month_note_max_length() -> None:
    """最大文字数ちょうどは許容する"""
    note = MonthNote.of(YearMonth(2024, 5), "あ" * MONTH_NOTE_MAX_LENGTH)

    assert len(note.note) == MONTH_NOTE_MAX_LENGTH


def test_month_note_too_long() -> None:
    """最大文字数を超える場合は例外"""
    with pytest.raises(ValueError):
        MonthNote.of(YearMonth(2024, 5), "あ" * (MONTH_NOTE_MAX_LENGTH + 1))
