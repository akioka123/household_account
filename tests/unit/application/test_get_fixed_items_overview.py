"""GetFixedItemsOverviewUseCase tests."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.port.card_repository import CardRepository
from app.application.port.fixed_item_history_repository import FixedItemHistoryRepository
from app.application.port.fixed_item_repository import FixedItemRepository
from app.application.port.logger import Logger
from app.application.usecase.get_fixed_items_overview import GetFixedItemsOverviewUseCase
from app.domain.model.card import Card
from app.domain.model.fixed_item import FixedItem
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


def _build_usecase(
    fixed_items: list[FixedItem],
    histories: list[FixedItemHistory],
    cards: list[Card] | None = None,
) -> GetFixedItemsOverviewUseCase:
    """モックリポジトリを差し込んだユースケースを作る"""
    fixed_item_repo = MagicMock(spec=FixedItemRepository)
    fixed_item_repo.find_all = AsyncMock(return_value=fixed_items)

    history_repo = MagicMock(spec=FixedItemHistoryRepository)
    history_repo.find_all = AsyncMock(return_value=histories)

    card_repo = MagicMock(spec=CardRepository)
    card_repo.find_all = AsyncMock(return_value=cards or [])

    logger = MagicMock(spec=Logger)
    logger.info = MagicMock()

    return GetFixedItemsOverviewUseCase(
        fixed_item_repo=fixed_item_repo,
        fixed_item_history_repo=history_repo,
        card_repo=card_repo,
        logger=logger,
    )


async def test_uses_latest_history_at_base_month() -> None:
    """UT-FIO-01: 基準年月以前で最新の履歴が現在額になる"""
    usecase = _build_usecase(
        fixed_items=[FixedItem(id=1, name="家賃")],
        histories=[
            _history(1, 1, 2024, 4, 80000),
            _history(2, 1, 2025, 4, 85000),
        ],
    )

    overview = await usecase.execute(YearMonth(2026, 8))

    assert len(overview.active_items) == 1
    assert overview.active_items[0].monthly_amount == Money(85000)
    assert overview.active_items[0].effective_from == YearMonth(2025, 4)


async def test_ignores_history_after_base_month() -> None:
    """UT-FIO-02: 基準年月より後の履歴は現在額に反映されない"""
    usecase = _build_usecase(
        fixed_items=[FixedItem(id=1, name="家賃")],
        histories=[
            _history(1, 1, 2024, 4, 80000),
            _history(2, 1, 2026, 12, 90000),
        ],
    )

    overview = await usecase.execute(YearMonth(2026, 8))

    assert overview.active_items[0].monthly_amount == Money(80000)


async def test_annual_amount_is_twelve_times_monthly() -> None:
    """UT-FIO-03: 年額換算は月額の12倍"""
    usecase = _build_usecase(
        fixed_items=[FixedItem(id=1, name="家賃")],
        histories=[_history(1, 1, 2024, 4, 80000)],
    )

    overview = await usecase.execute(YearMonth(2026, 8))

    assert overview.active_items[0].annual_amount == Money(960000)
    assert overview.annual_total == Money(960000)


async def test_sorted_by_amount_desc_then_name() -> None:
    """UT-FIO-04: 月額降順、同額は項目名の昇順に並ぶ"""
    usecase = _build_usecase(
        fixed_items=[
            FixedItem(id=1, name="サブスクB"),
            FixedItem(id=2, name="家賃"),
            FixedItem(id=3, name="サブスクA"),
        ],
        histories=[
            _history(1, 1, 2024, 4, 1000),
            _history(2, 2, 2024, 4, 80000),
            _history(3, 3, 2024, 4, 1000),
        ],
    )

    overview = await usecase.execute(YearMonth(2026, 8))

    assert [item.name for item in overview.active_items] == ["家賃", "サブスクA", "サブスクB"]


async def test_totals_cover_active_items_only() -> None:
    """UT-FIO-05: 合計は有効な項目のみを対象にする"""
    usecase = _build_usecase(
        fixed_items=[FixedItem(id=1, name="家賃"), FixedItem(id=2, name="解約済み")],
        histories=[
            _history(1, 1, 2024, 4, 80000),
            _history(2, 2, 2024, 4, 5000),
            _history(3, 2, 2025, 1, 0),
        ],
    )

    overview = await usecase.execute(YearMonth(2026, 8))

    assert overview.monthly_total == Money(80000)
    assert overview.active_count == 1


async def test_ended_item_is_separated() -> None:
    """UT-FIO-06: 金額0が最新の項目は運用終了として分離される"""
    usecase = _build_usecase(
        fixed_items=[FixedItem(id=1, name="解約済み")],
        histories=[
            _history(1, 1, 2024, 4, 5000),
            _history(2, 1, 2025, 1, 0),
        ],
    )

    overview = await usecase.execute(YearMonth(2026, 8))

    assert overview.active_items == []
    assert len(overview.ended_items) == 1
    assert overview.ended_items[0].name == "解約済み"
    assert overview.ended_items[0].monthly_amount == Money(0)
    assert overview.monthly_total == Money(0)


async def test_restarted_item_returns_to_active() -> None:
    """UT-FIO-07: 運用終了後に再開した項目は有効に戻る"""
    usecase = _build_usecase(
        fixed_items=[FixedItem(id=1, name="サブスク")],
        histories=[
            _history(1, 1, 2024, 4, 5000),
            _history(2, 1, 2025, 1, 0),
            _history(3, 1, 2025, 6, 6000),
        ],
    )

    overview = await usecase.execute(YearMonth(2026, 8))

    assert len(overview.active_items) == 1
    assert overview.active_items[0].monthly_amount == Money(6000)
    assert overview.ended_items == []


async def test_history_diff_from_previous() -> None:
    """UT-FIO-08: 改定履歴の前回差分。初回はNone、減額は負の値"""
    usecase = _build_usecase(
        fixed_items=[FixedItem(id=1, name="通信費")],
        histories=[
            _history(1, 1, 2024, 4, 5000),
            _history(2, 1, 2025, 1, 6500),
            _history(3, 1, 2025, 6, 4000),
        ],
    )

    overview = await usecase.execute(YearMonth(2026, 8))

    diffs = [h.diff_from_previous for h in overview.active_items[0].histories]
    assert diffs == [None, 1500, -2500]


async def test_card_name_is_none_when_unlinked_or_missing() -> None:
    """UT-FIO-09: 未紐づけ・存在しないカードIDではカード名がNoneになる"""
    usecase = _build_usecase(
        fixed_items=[FixedItem(id=1, name="未紐づけ"), FixedItem(id=2, name="削除済みカード")],
        histories=[
            _history(1, 1, 2024, 4, 1000, card_id=None),
            _history(2, 2, 2024, 4, 2000, card_id=99),
        ],
        cards=[Card(id=1, name="メインカード", enabled=True)],
    )

    overview = await usecase.execute(YearMonth(2026, 8))

    assert all(item.card_name is None for item in overview.active_items)


async def test_share_percent() -> None:
    """UT-FIO-10: 割合が算出される"""
    usecase = _build_usecase(
        fixed_items=[FixedItem(id=1, name="家賃"), FixedItem(id=2, name="通信費")],
        histories=[
            _history(1, 1, 2024, 4, 75000),
            _history(2, 2, 2024, 4, 25000),
        ],
    )

    overview = await usecase.execute(YearMonth(2026, 8))

    assert overview.active_items[0].share_percent == pytest.approx(75.0)
    assert overview.active_items[1].share_percent == pytest.approx(25.0)


async def test_share_percent_is_none_when_total_is_zero() -> None:
    """UT-FIO-10: 月額合計が0のときは割合がNoneになる"""
    usecase = _build_usecase(
        fixed_items=[FixedItem(id=1, name="解約済み")],
        histories=[_history(1, 1, 2024, 4, 0)],
    )

    overview = await usecase.execute(YearMonth(2026, 8))

    assert overview.monthly_total == Money(0)
    assert overview.ended_items[0].share_percent is None


async def test_months_since_change_across_years() -> None:
    """UT-FIO-11: 経過月数が年をまたいでも正しい"""
    usecase = _build_usecase(
        fixed_items=[FixedItem(id=1, name="家賃")],
        histories=[_history(1, 1, 2025, 11, 80000)],
    )

    overview = await usecase.execute(YearMonth(2026, 2))

    assert overview.active_items[0].months_since_change == 3


async def test_empty_when_no_fixed_items() -> None:
    """UT-FIO-12: 固定費が0件のときは空の結果を返す"""
    usecase = _build_usecase(fixed_items=[], histories=[])

    overview = await usecase.execute(YearMonth(2026, 8))

    assert overview.active_items == []
    assert overview.ended_items == []
    assert overview.monthly_total == Money(0)
    assert overview.annual_total == Money(0)
    assert overview.active_count == 0


async def test_histories_are_not_filtered_by_base_month() -> None:
    """UT-FIO-13: 改定履歴は基準年月で絞り込まれない（現在額には効かない）"""
    usecase = _build_usecase(
        fixed_items=[FixedItem(id=1, name="家賃")],
        histories=[
            _history(1, 1, 2024, 4, 80000),
            _history(2, 1, 2026, 12, 90000),
        ],
    )

    overview = await usecase.execute(YearMonth(2026, 8))

    item = overview.active_items[0]
    assert item.monthly_amount == Money(80000)
    assert [h.effective_from for h in item.histories] == [
        YearMonth(2024, 4),
        YearMonth(2026, 12),
    ]
