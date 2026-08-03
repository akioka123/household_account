"""固定費棚卸し画面の結合テスト"""

from __future__ import annotations

from datetime import datetime

from fastapi.testclient import TestClient

from app.application.usecase.get_fixed_items_overview import (
    FixedItemHistoryView,
    FixedItemOverview,
    FixedItemsOverview,
)
from app.domain.model.money import Money
from app.domain.model.year_month import YearMonth
from app.main import app
from app.presentation.web.routers.fixed_items_router import (
    provide_get_fixed_items_overview_uc,
)


class StubGetFixedItemsOverviewUseCase:
    """DBを使わないGetFixedItemsOverviewUseCaseのスタブ"""

    def __init__(self) -> None:
        self.called_with: YearMonth | None = None

    async def execute(self, base_ym: YearMonth) -> FixedItemsOverview:
        self.called_with = base_ym
        item = FixedItemOverview(
            fixed_item_id=1,
            name="家賃",
            monthly_amount=Money(85000),
            annual_amount=Money(1020000),
            share_percent=100.0,
            card_name=None,
            included_in_card=False,
            effective_from=YearMonth(2025, 4),
            months_since_change=16,
            histories=[
                FixedItemHistoryView(
                    effective_from=YearMonth(2024, 4),
                    amount=Money(80000),
                    diff_from_previous=None,
                    card_name=None,
                    is_ended=False,
                ),
                FixedItemHistoryView(
                    effective_from=YearMonth(2025, 4),
                    amount=Money(85000),
                    diff_from_previous=5000,
                    card_name=None,
                    is_ended=False,
                ),
            ],
        )
        return FixedItemsOverview(
            base_ym=base_ym,
            active_items=[item],
            ended_items=[],
            monthly_total=Money(85000),
            annual_total=Money(1020000),
            active_count=1,
        )


def _client(usecase: StubGetFixedItemsOverviewUseCase) -> TestClient:
    """スタブを注入したTestClientを作成"""
    app.dependency_overrides[provide_get_fixed_items_overview_uc] = lambda: usecase
    return TestClient(app)


def test_fixed_items_page_defaults_to_current_month() -> None:
    """IT-FI-01: 基準年月を省略すると当月が使われる"""
    usecase = StubGetFixedItemsOverviewUseCase()

    try:
        with _client(usecase) as client:
            response = client.get("/fixed-items")
    finally:
        app.dependency_overrides.clear()

    now = datetime.now()
    assert response.status_code == 200
    assert usecase.called_with == YearMonth(now.year, now.month)
    assert "固定費一覧" in response.text
    assert "85,000円" in response.text
    assert "1,020,000円" in response.text


def test_fixed_items_page_accepts_base_year_month() -> None:
    """IT-FI-02: 基準年月を指定するとその年月で集計される"""
    usecase = StubGetFixedItemsOverviewUseCase()

    try:
        with _client(usecase) as client:
            response = client.get("/fixed-items", params={"ym": "2025-03"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert usecase.called_with == YearMonth(2025, 3)
    assert "2025年3月時点" in response.text


def test_fixed_items_page_falls_back_on_invalid_year_month() -> None:
    """IT-FI-03: 不正な基準年月は当月にフォールバックする"""
    now = datetime.now()

    for invalid in ("abc", "2025-13", "2025", ""):
        usecase = StubGetFixedItemsOverviewUseCase()
        try:
            with _client(usecase) as client:
                response = client.get("/fixed-items", params={"ym": invalid})
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 200, invalid
        assert usecase.called_with == YearMonth(now.year, now.month), invalid


def test_fixed_items_page_returns_partial_for_htmx() -> None:
    """IT-FI-04: HX-Requestヘッダ付きの場合は本体のみを返す"""
    usecase = StubGetFixedItemsOverviewUseCase()

    try:
        with _client(usecase) as client:
            response = client.get("/fixed-items", headers={"HX-Request": "true"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert "<html" not in response.text
    assert 'id="fixed-items-content"' in response.text
