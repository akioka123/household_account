"""FixedItemHistoryのテスト"""
from __future__ import annotations

from app.domain.model.fixed_item_history import FixedItemHistory
from app.domain.model.money import Money
from app.domain.model.year_month import YearMonth


def test_fixed_item_history_creation() -> None:
    """FixedItemHistoryの作成"""
    ym = YearMonth(2024, 3)
    history = FixedItemHistory(
        id=1,
        fixed_item_id=1,
        effective_from=ym,
        amount=Money(100000),
        card_id=None,
        included_in_card=False,
    )
    assert history.id == 1
    assert history.fixed_item_id == 1
    assert history.effective_from == ym
    assert history.amount.amount == 100000
    assert history.card_id is None
    assert history.included_in_card is False


def test_fixed_item_history_with_card() -> None:
    """カード紐づけありのFixedItemHistory"""
    ym = YearMonth(2024, 3)
    history = FixedItemHistory(
        id=1,
        fixed_item_id=1,
        effective_from=ym,
        amount=Money(50000),
        card_id=2,
        included_in_card=True,
    )
    assert history.card_id == 2
    assert history.included_in_card is True


def test_fixed_item_history_is_active_at() -> None:
    """適用開始年月での有効性判定"""
    ym = YearMonth(2024, 3)
    history = FixedItemHistory(
        id=1,
        fixed_item_id=1,
        effective_from=ym,
        amount=Money(100000),
        card_id=None,
        included_in_card=False,
    )
    # 適用開始年月と同じ
    assert history.is_active_at(YearMonth(2024, 3)) is True
    # 適用開始年月より後
    assert history.is_active_at(YearMonth(2024, 4)) is True
    assert history.is_active_at(YearMonth(2025, 1)) is True
    # 適用開始年月より前
    assert history.is_active_at(YearMonth(2024, 2)) is False
    assert history.is_active_at(YearMonth(2023, 12)) is False


def test_fixed_item_history_is_deleted() -> None:
    """削除済み判定"""
    ym = YearMonth(2024, 3)
    # 金額0の場合は削除済み
    deleted_history = FixedItemHistory(
        id=1,
        fixed_item_id=1,
        effective_from=ym,
        amount=Money(0),
        card_id=None,
        included_in_card=False,
    )
    assert deleted_history.is_deleted() is True

    # 金額がある場合は削除されていない
    active_history = FixedItemHistory(
        id=2,
        fixed_item_id=1,
        effective_from=ym,
        amount=Money(100000),
        card_id=None,
        included_in_card=False,
    )
    assert active_history.is_deleted() is False
