"""年次ダッシュボードのCSV出力"""
from __future__ import annotations

import csv
import io

from app.application.usecase.get_dashboard_data import DashboardData
from app.domain.model.living_expense import LIVING_EXPENSE_CATEGORIES

# Excelで文字化けさせないためのUTF-8 BOM
UTF8_BOM = "﻿"


def build_annual_csv(
    dashboard_data: DashboardData,
    living_category_labels: dict[str, str],
) -> str:
    """年次ダッシュボードの全体をCSV文字列に変換

    Args:
        dashboard_data: ダッシュボード表示用データ
        living_category_labels: 生活費カテゴリの表示ラベル

    Returns:
        UTF-8 BOM付きのCSV文字列（月次行 → 集計行 → 平均行）
    """
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")

    header = [
        "年月",
        "手取り収入",
        "固定費",
        "変動費",
        "現金支出",
        "カード変動費",
        "生活費合計",
        *[living_category_labels[cat] for cat in LIVING_EXPENSE_CATEGORIES],
        "損益",
        "変動費平均差",
        "メモ",
    ]
    writer.writerow(header)

    summaries = dashboard_data.month_summaries
    for summary in summaries:
        ym = summary.year_month
        by_cat = dashboard_data.living_expenses_by_month.get(ym, {})
        writer.writerow(
            [
                ym.to_string(),
                summary.net_income.amount,
                summary.fixed_total.amount,
                summary.variable_total.amount,
                summary.cash_spent.amount,
                summary.variable_card.amount,
                dashboard_data.living_total(ym),
                *[by_cat.get(cat).amount if by_cat.get(cat) else 0 for cat in LIVING_EXPENSE_CATEGORIES],
                summary.profit.amount,
                dashboard_data.variable_diff(ym),
                dashboard_data.note_text(ym),
            ]
        )

    writer.writerow(_aggregate_row("集計", dashboard_data))
    writer.writerow(_average_row("平均", dashboard_data))

    return UTF8_BOM + buffer.getvalue()


def _aggregate_row(label: str, dashboard_data: DashboardData) -> list[object]:
    """年間の集計行を作成"""
    summaries = dashboard_data.month_summaries
    living_by_cat = {
        cat: sum(
            dashboard_data.living_expenses_by_month.get(s.year_month, {}).get(cat).amount
            if dashboard_data.living_expenses_by_month.get(s.year_month, {}).get(cat)
            else 0
            for s in summaries
        )
        for cat in LIVING_EXPENSE_CATEGORIES
    }
    return [
        label,
        sum(s.net_income.amount for s in summaries),
        sum(s.fixed_total.amount for s in summaries),
        sum(s.variable_total.amount for s in summaries),
        sum(s.cash_spent.amount for s in summaries),
        sum(s.variable_card.amount for s in summaries),
        sum(dashboard_data.living_total(s.year_month) for s in summaries),
        *[living_by_cat[cat] for cat in LIVING_EXPENSE_CATEGORIES],
        sum(s.profit.amount for s in summaries),
        "",
        "",
    ]


def _average_row(label: str, dashboard_data: DashboardData) -> list[object]:
    """月平均行を作成（サマリのある月のみを対象、小数は切り捨て）"""
    summaries = dashboard_data.month_summaries
    count = len(summaries)
    aggregate = _aggregate_row(label, dashboard_data)

    if count == 0:
        return aggregate

    # 先頭のラベルと末尾2列（変動費平均差・メモ）以外を月数で割る
    averaged: list[object] = [label]
    for value in aggregate[1:-2]:
        averaged.append(int(value) // count)
    averaged.extend(["", ""])
    return averaged
