"""月次メモ保存エンドポイントの結合テスト"""
from __future__ import annotations

from fastapi.testclient import TestClient

from app.application.usecase.get_month_summary import MonthSummaryResult
from app.application.usecase.manage_month_note import SaveMonthNoteCommand
from app.domain.model.money import Money
from app.domain.model.month_note import MONTH_NOTE_MAX_LENGTH, MonthNote
from app.domain.model.month_summary import MonthSummary
from app.domain.model.year_month import YearMonth
from app.main import app
from app.presentation.web.routers.month_router import (
    provide_get_month_summary_uc,
    provide_manage_month_note_uc,
)


class StubGetMonthSummaryUseCase:
    """DBを使わないGetMonthSummaryUseCaseのスタブ"""

    async def execute(self, year: int, month: int) -> MonthSummaryResult:
        summary = MonthSummary(
            year_month=YearMonth(year, month),
            net_income=Money(400000),
            fixed_total=Money(100000),
            variable_total=Money(150000),
            profit=Money(150000),
            cash_spent=Money(50000),
            variable_card=Money(100000),
        )
        return MonthSummaryResult(
            summary=summary,
            warnings=[],
            cash_spent_uncertain=False,
            variable_card_negative=False,
        )


class StubManageMonthNoteUseCase:
    """DBを使わないManageMonthNoteUseCaseのスタブ（メモをメモリに保持）"""

    def __init__(self) -> None:
        self.notes: dict[YearMonth, MonthNote] = {}

    async def get_note(self, year: int, month: int) -> MonthNote | None:
        return self.notes.get(YearMonth(year, month))

    async def save_note(self, command: SaveMonthNoteCommand) -> MonthNote | None:
        ym = YearMonth(command.year, command.month)
        note = MonthNote.of(ym, command.note)
        if note.is_empty():
            self.notes.pop(ym, None)
            return None
        self.notes[ym] = note
        return note


def _client(note_uc: StubManageMonthNoteUseCase) -> TestClient:
    """スタブを注入したTestClientを作成"""
    app.dependency_overrides[provide_get_month_summary_uc] = StubGetMonthSummaryUseCase
    app.dependency_overrides[provide_manage_month_note_uc] = lambda: note_uc
    return TestClient(app)


def test_save_month_note() -> None:
    """メモを保存すると集計タブに反映される"""
    note_uc = StubManageMonthNoteUseCase()

    try:
        with _client(note_uc) as client:
            response = client.post("/month/2024/5/note", data={"note": "帰省で交通費が増えた"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert "メモを保存しました。" in response.text
    assert "帰省で交通費が増えた" in response.text
    assert note_uc.notes[YearMonth(2024, 5)].note == "帰省で交通費が増えた"


def test_save_month_note_empty_deletes() -> None:
    """空欄で保存するとメモが削除される"""
    note_uc = StubManageMonthNoteUseCase()
    note_uc.notes[YearMonth(2024, 5)] = MonthNote.of(YearMonth(2024, 5), "旧メモ")

    try:
        with _client(note_uc) as client:
            response = client.post("/month/2024/5/note", data={"note": ""})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert YearMonth(2024, 5) not in note_uc.notes
    assert "旧メモ" not in response.text


def test_save_month_note_too_long_shows_error() -> None:
    """最大文字数を超える場合はエラーメッセージを表示する"""
    note_uc = StubManageMonthNoteUseCase()

    try:
        with _client(note_uc) as client:
            response = client.post(
                "/month/2024/5/note",
                data={"note": "あ" * (MONTH_NOTE_MAX_LENGTH + 1)},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert f"メモは{MONTH_NOTE_MAX_LENGTH}文字以内で入力してください。" in response.text
    assert note_uc.notes == {}


def test_summary_tab_shows_saved_note() -> None:
    """集計タブに保存済みメモが表示される"""
    note_uc = StubManageMonthNoteUseCase()
    note_uc.notes[YearMonth(2024, 5)] = MonthNote.of(YearMonth(2024, 5), "特別な出費はなし")

    try:
        with _client(note_uc) as client:
            response = client.get("/month/2024/5/tab/summary")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert "特別な出費はなし" in response.text
    assert "消費理由メモ" in response.text
