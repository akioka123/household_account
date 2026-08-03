"""年次ダッシュボードCSV出力エンドポイントの結合テスト"""
from __future__ import annotations

import csv
import io

from fastapi.testclient import TestClient

from app.application.usecase.get_dashboard_data import DashboardData
from app.domain.model.living_expense import LIVING_EXPENSE_CATEGORIES
from app.domain.model.money import Money
from app.domain.model.month_note import MonthNote
from app.domain.model.month_summary import MonthSummary
from app.domain.model.year_month import YearMonth
from app.main import app
from app.presentation.web.routers.dashboard_router import provide_get_dashboard_data_uc


class StubGetDashboardDataUseCase:
    """DBを使わないGetDashboardDataUseCaseのスタブ"""

    def __init__(self, dashboard_data: DashboardData) -> None:
        self._dashboard_data = dashboard_data

    async def execute(self, year: int) -> DashboardData:
        return self._dashboard_data


def _dashboard_data() -> DashboardData:
    """テスト用のダッシュボードデータ（1ヶ月分）"""
    ym = YearMonth(2024, 1)
    summary = MonthSummary(
        year_month=ym,
        net_income=Money(400000),
        fixed_total=Money(100000),
        variable_total=Money(150000),
        profit=Money(150000),
        cash_spent=Money(50000),
        variable_card=Money(100000),
    )
    living = {cat: Money(0) for cat in LIVING_EXPENSE_CATEGORIES}
    living["food"] = Money(12000)

    return DashboardData(
        year=2024,
        month_summaries=[summary],
        annual_gross=500000,
        annual_net=400000,
        living_expenses_by_month={ym: living},
        month_notes={ym: MonthNote(id=1, year_month=ym, note="帰省で交通費が増えた")},
        variable_average=150000,
    )


def test_export_dashboard_csv() -> None:
    """CSVダウンロードのレスポンス内容を検証"""
    app.dependency_overrides[provide_get_dashboard_data_uc] = lambda: StubGetDashboardDataUseCase(
        _dashboard_data()
    )

    try:
        with TestClient(app) as client:
            response = client.get("/dashboard/2024/export.csv")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert response.headers["content-disposition"] == 'attachment; filename="dashboard_2024.csv"'

    body = response.content.decode("utf-8-sig")
    rows = list(csv.reader(io.StringIO(body)))

    assert rows[0][0] == "年月"
    assert rows[1][0] == "2024-01"
    assert rows[1][4] == "50000"  # 現金支出
    assert rows[1][5] == "100000"  # カード変動費
    assert rows[1][6] == "12000"  # 生活費合計
    assert rows[1][14] == "帰省で交通費が増えた"  # メモ
    assert rows[2][0] == "集計"
    assert rows[3][0] == "平均"
