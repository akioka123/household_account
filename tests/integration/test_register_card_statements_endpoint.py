"""カード請求登録エンドポイントの結合テスト（MN-004再発防止）"""
from __future__ import annotations

from fastapi.testclient import TestClient

from app.application.usecase.register_card_statements import CardStatementCommand
from app.domain.model.card import Card
from app.domain.model.card_statement import CardStatement
from app.domain.model.year_month import YearMonth
from app.main import app
from app.presentation.web.routers.month_router import (
    provide_card_statement_repo,
    provide_manage_cards_uc,
    provide_register_card_statements_uc,
)


class StubRegisterCardStatementsUseCase:
    """実行時に渡されたcommandsを記録するスタブ"""

    def __init__(self) -> None:
        self.executed_commands: list[CardStatementCommand] | None = None

    async def execute(
        self, year: int, month: int, commands: list[CardStatementCommand]
    ) -> None:
        self.executed_commands = commands


class StubCardStatementRepo:
    async def find_by_year_month(self, ym: YearMonth) -> list[CardStatement]:
        return []


class StubManageCardsUseCase:
    async def get_all_cards(self) -> list[Card]:
        return [Card(id=1, name="テストカード", enabled=True)]


def _client(usecase: StubRegisterCardStatementsUseCase) -> TestClient:
    app.dependency_overrides[provide_register_card_statements_uc] = lambda: usecase
    app.dependency_overrides[provide_card_statement_repo] = lambda: StubCardStatementRepo()
    app.dependency_overrides[provide_manage_cards_uc] = lambda: StubManageCardsUseCase()
    return TestClient(app)


def test_register_card_statements_keeps_zero_amount_row() -> None:
    """0円で請求額を訂正した行がサイレントに無視されず登録対象に含まれる"""
    usecase = StubRegisterCardStatementsUseCase()

    try:
        with _client(usecase) as client:
            response = client.post(
                "/month/2024/5/card-statements",
                data={"card_id_0": "1", "amount_0": "0"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert usecase.executed_commands == [CardStatementCommand(card_id=1, amount=0)]


def test_register_card_statements_drops_negative_amount_row() -> None:
    """負の請求額は（フォームに下限制約が無いため）router側で従来どおり除外される"""
    usecase = StubRegisterCardStatementsUseCase()

    try:
        with _client(usecase) as client:
            response = client.post(
                "/month/2024/5/card-statements",
                data={"card_id_0": "1", "amount_0": "-1"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert usecase.executed_commands == []
