"""金額0以上バリデーションの結合テスト（MN-002再発防止）"""
from __future__ import annotations

from fastapi.testclient import TestClient

from app.application.usecase.register_income import RegisterIncomeCommand
from app.domain.model.income import Income
from app.domain.model.year_month import YearMonth
from app.main import app
from app.presentation.web.routers.month_router import (
    provide_income_repo,
    provide_register_income_uc,
)


class StubRegisterIncomeUseCase:
    """呼ばれたかどうかだけを記録するスタブ"""

    def __init__(self) -> None:
        self.executed_with: RegisterIncomeCommand | None = None

    async def execute(self, command: RegisterIncomeCommand) -> None:
        self.executed_with = command
        raise AssertionError("バリデーションで弾かれるべきでusecaseは呼ばれないはず")


class StubIncomeRepo:
    async def find(self, ym: YearMonth) -> Income | None:
        return None


def _client(usecase: StubRegisterIncomeUseCase) -> TestClient:
    app.dependency_overrides[provide_register_income_uc] = lambda: usecase
    app.dependency_overrides[provide_income_repo] = lambda: StubIncomeRepo()
    return TestClient(app)


def test_register_income_rejects_negative_amount() -> None:
    """収入登録で負の金額はFastAPIのバリデーションで422になり、usecaseは呼ばれない"""
    usecase = StubRegisterIncomeUseCase()

    try:
        with _client(usecase) as client:
            response = client.post(
                "/month/2024/5/income",
                data={
                    "salary_gross": -1,
                    "salary_net": 300000,
                    "bonus_gross": 0,
                    "bonus_net": 0,
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert usecase.executed_with is None
