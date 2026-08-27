"""FixedExpenses集約のテスト"""

from __future__ import annotations

from app.domain.model.fixed_expenses import FixedExpenses
from app.domain.model.fixed_item_history import FixedItemHistory
from app.domain.model.money import Money
from app.domain.model.year_month import YearMonth


def _history(
    history_id: int,
    fixed_item_id: int,
    year: int,
    month: int,
    amount: int,
    card_id: int | None = None,
    included_in_card: bool = False,
) -> FixedItemHistory:
    """テスト用の固定費履歴を作る"""
    return FixedItemHistory(
        id=history_id,
        fixed_item_id=fixed_item_id,
        effective_from=YearMonth(year, month),
        amount=Money(amount),
        card_id=card_id,
        included_in_card=included_in_card,
    )


def test_calculate_uses_latest_history_per_item() -> None:
    """UT-FE-01: 項目ごとに最新の履歴だけを合計する"""
    fixed_expenses = FixedExpenses(
        [
            _history(1, 1, 2024, 4, 80000),
            _history(2, 1, 2025, 4, 85000),
            _history(3, 2, 2024, 4, 3000),
        ]
    )

    assert fixed_expenses.calculate() == Money(88000)


def test_calculate_excludes_ended_items() -> None:
    """UT-FE-02: 金額0（運用終了）は合計から除外される"""
    fixed_expenses = FixedExpenses(
        [
            _history(1, 1, 2024, 4, 80000),
            _history(2, 2, 2024, 4, 3000),
            _history(3, 2, 2025, 1, 0),
        ]
    )

    assert fixed_expenses.calculate() == Money(80000)


def test_by_card_aggregates_only_included_in_card() -> None:
    """UT-FE-03: カード請求に含まれ、かつカード紐づけがあるものだけ集計する"""
    fixed_expenses = FixedExpenses(
        [
            _history(1, 1, 2024, 4, 5000, card_id=1, included_in_card=True),
            _history(2, 2, 2024, 4, 3000, card_id=1, included_in_card=True),
            _history(3, 3, 2024, 4, 7000, card_id=2, included_in_card=False),
            _history(4, 4, 2024, 4, 9000, card_id=None, included_in_card=True),
        ]
    )

    assert fixed_expenses.by_card() == {1: Money(8000)}


def test_get_effective_histories_returns_latest_per_item() -> None:
    """UT-FE-04: 項目ごとに適用開始年月が最大の1件を返す"""
    fixed_expenses = FixedExpenses(
        [
            _history(1, 1, 2024, 4, 80000),
            _history(2, 1, 2025, 4, 85000),
            _history(3, 2, 2024, 4, 3000),
        ]
    )

    effective = fixed_expenses.get_effective_histories()

    assert len(effective) == 2
    by_item = {h.fixed_item_id: h for h in effective}
    assert by_item[1].effective_from == YearMonth(2025, 4)
    assert by_item[2].effective_from == YearMonth(2024, 4)


def test_by_card_uses_latest_history_per_item() -> None:
    """UT-FE-06: 改定履歴が複数あっても最新の1件のみをカード別集計に使う（二重集計の回帰防止）"""
    fixed_expenses = FixedExpenses(
        [
            _history(1, 1, 2024, 4, 5000, card_id=1, included_in_card=True),
            _history(2, 1, 2025, 4, 6000, card_id=1, included_in_card=True),
        ]
    )

    assert fixed_expenses.by_card() == {1: Money(6000)}


def test_by_card_excludes_ended_items() -> None:
    """UT-FE-07: 金額0（運用終了）の履歴はカード別集計からも除外される"""
    fixed_expenses = FixedExpenses(
        [
            _history(1, 1, 2024, 4, 5000, card_id=1, included_in_card=True),
            _history(2, 1, 2025, 4, 0, card_id=1, included_in_card=True),
        ]
    )

    assert fixed_expenses.by_card() == {}


def test_empty_histories() -> None:
    """UT-FE-05: 履歴が空のときは合計0・カード別集計は空"""
    fixed_expenses = FixedExpenses([])

    assert fixed_expenses.calculate() == Money(0)
    assert fixed_expenses.by_card() == {}
    assert fixed_expenses.get_effective_histories() == []
