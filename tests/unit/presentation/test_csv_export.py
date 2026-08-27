"""年次ダッシュボードCSV出力のテスト"""
from __future__ import annotations

import csv
import io

from app.application.usecase.get_dashboard_data import DashboardData
from app.domain.model.living_expense import (
    LIVING_EXPENSE_CATEGORIES,
    LIVING_EXPENSE_CATEGORY_ELECTRICITY,
    LIVING_EXPENSE_CATEGORY_FOOD,
)
from app.domain.model.money import Money
from app.domain.model.month_note import MonthNote
from app.domain.model.month_summary import MonthSummary
from app.domain.model.year_month import YearMonth
from app.presentation.web.csv_export import UTF8_BOM, build_annual_csv

LABELS = {
    "food": "食費",
    "electricity": "電気代",
    "gas": "ガス代",
    "mobile": "携帯料金",
    "communication": "通信費",
}


def _living(food: int = 0, electricity: int = 0) -> dict[str, Money]:
    """カテゴリ別生活費を作成（未指定のカテゴリは0円）"""
    by_cat = {cat: Money(0) for cat in LIVING_EXPENSE_CATEGORIES}
    by_cat[LIVING_EXPENSE_CATEGORY_FOOD] = Money(food)
    by_cat[LIVING_EXPENSE_CATEGORY_ELECTRICITY] = Money(electricity)
    return by_cat


def _dashboard_data() -> DashboardData:
    """テスト用のダッシュボードデータ（2ヶ月分）"""
    ym1 = YearMonth(2024, 1)
    ym2 = YearMonth(2024, 2)
    summaries = [
        MonthSummary(
            year_month=ym1,
            net_income=Money(400000),
            fixed_total=Money(100000),
            variable_total=Money(150000),
            profit=Money(150000),
            cash_spent=Money(50000),
            variable_card=Money(100000),
        ),
        MonthSummary(
            year_month=ym2,
            net_income=Money(400000),
            fixed_total=Money(100000),
            variable_total=Money(200000),
            profit=Money(100000),
            cash_spent=Money(60000),
            variable_card=Money(140000),
        ),
    ]
    return DashboardData(
        year=2024,
        month_summaries=summaries,
        annual_gross=1000000,
        annual_net=800000,
        living_expenses_by_month={
            ym1: _living(food=12000, electricity=8000),
            ym2: _living(food=10000),
        },
        month_notes={ym2: MonthNote(id=1, year_month=ym2, note="家電の買い替えで支出増")},
        variable_average=175000,
    )


def _parse(csv_text: str) -> list[list[str]]:
    """CSV文字列を行のリストに変換（BOMは除去）"""
    body = csv_text[len(UTF8_BOM):] if csv_text.startswith(UTF8_BOM) else csv_text
    return list(csv.reader(io.StringIO(body)))


def test_build_annual_csv_has_bom() -> None:
    """ExcelのためにUTF-8 BOMを先頭に付与する"""
    csv_text = build_annual_csv(_dashboard_data(), LABELS)

    assert csv_text.startswith(UTF8_BOM)


def test_build_annual_csv_header() -> None:
    """ヘッダに内訳・平均差・メモの列を含む"""
    rows = _parse(build_annual_csv(_dashboard_data(), LABELS))

    assert rows[0] == [
        "年月",
        "手取り収入",
        "固定費",
        "変動費",
        "現金支出",
        "カード変動費",
        "生活費合計",
        "食費",
        "電気代",
        "ガス代",
        "携帯料金",
        "通信費",
        "損益",
        "変動費平均差",
        "メモ",
    ]


def test_build_annual_csv_month_rows() -> None:
    """月次行に内訳・平均差・メモを出力する"""
    rows = _parse(build_annual_csv(_dashboard_data(), LABELS))

    assert rows[1] == [
        "2024-01",
        "400000",
        "100000",
        "150000",
        "50000",
        "100000",
        "20000",
        "12000",
        "8000",
        "0",
        "0",
        "0",
        "150000",
        "-25000",
        "",
    ]
    assert rows[2][0] == "2024-02"
    assert rows[2][13] == "25000"  # 変動費平均差
    assert rows[2][14] == "家電の買い替えで支出増"


def test_build_annual_csv_aggregate_and_average_rows() -> None:
    """集計行と平均行を出力する"""
    rows = _parse(build_annual_csv(_dashboard_data(), LABELS))

    aggregate = rows[3]
    assert aggregate[0] == "集計"
    assert aggregate[1] == "800000"  # 手取り収入
    assert aggregate[3] == "350000"  # 変動費
    assert aggregate[4] == "110000"  # 現金支出
    assert aggregate[5] == "240000"  # カード変動費
    assert aggregate[6] == "30000"  # 生活費合計
    assert aggregate[12] == "250000"  # 損益

    average = rows[4]
    assert average[0] == "平均"
    assert average[3] == "175000"  # 変動費の月平均
    assert average[6] == "15000"  # 生活費の月平均


def test_build_annual_csv_without_data() -> None:
    """データがない年でもヘッダと集計・平均行を出力する"""
    empty = DashboardData(
        year=2024,
        month_summaries=[],
        annual_gross=0,
        annual_net=0,
        living_expenses_by_month={},
        month_notes={},
        variable_average=0,
    )

    rows = _parse(build_annual_csv(empty, LABELS))

    assert len(rows) == 3
    assert rows[1][0] == "集計"
    assert rows[1][1] == "0"
    assert rows[2][0] == "平均"
