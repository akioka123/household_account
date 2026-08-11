"""同一年月の固定費履歴が上書きされることのテスト

FixedItemHistoryRepository は「同一項目・同一適用開始年月なら上書き」という契約を持つ
（DB側は UNIQUE(fixed_item_id, effective_from) で保証。マイグレーション009）。
ここでは契約どおりのFakeを使い、ユースケース経由で訂正が反映されることを確認する。
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from app.application.port.fixed_item_repository import FixedItemRepository
from app.application.port.logger import Logger
from app.application.usecase.manage_fixed_items import (
    AddFixedItemHistoryCommand,
    EndFixedItemOperationCommand,
    ManageFixedItemsUseCase,
)
from app.domain.model.fixed_expenses import FixedExpenses
from app.domain.model.fixed_item import FixedItem
from app.domain.model.fixed_item_history import FixedItemHistory
from app.domain.model.money import Money
from app.domain.model.year_month import YearMonth


class FakeFixedItemHistoryRepository:
    """(fixed_item_id, effective_from) をキーに上書きするFake"""

    def __init__(self) -> None:
        self.histories: list[FixedItemHistory] = []

    async def find_all(self) -> list[FixedItemHistory]:
        return list(self.histories)

    async def find_by_fixed_item_id(self, fixed_item_id: int) -> list[FixedItemHistory]:
        return [h for h in self.histories if h.fixed_item_id == fixed_item_id]

    async def find_active_at(self, ym: YearMonth) -> list[FixedItemHistory]:
        return [h for h in self.histories if h.is_active_at(ym)]

    async def save(self, history: FixedItemHistory) -> None:
        for index, existing in enumerate(self.histories):
            if (
                existing.fixed_item_id == history.fixed_item_id
                and existing.effective_from == history.effective_from
            ):
                # 既存IDを保ったまま内容を上書きする
                self.histories[index] = FixedItemHistory(
                    id=existing.id,
                    fixed_item_id=history.fixed_item_id,
                    effective_from=history.effective_from,
                    amount=history.amount,
                    card_id=history.card_id,
                    included_in_card=history.included_in_card,
                )
                return
        self.histories.append(history)


def _build_usecase(
    history_repo: FakeFixedItemHistoryRepository,
) -> ManageFixedItemsUseCase:
    """Fakeを差し込んだユースケースを作る"""
    fixed_item_repo = MagicMock(spec=FixedItemRepository)
    fixed_item_repo.find_all = AsyncMock(return_value=[FixedItem(id=1, name="家賃")])
    fixed_item_repo.find_by_id = AsyncMock(return_value=FixedItem(id=1, name="家賃"))

    logger = MagicMock(spec=Logger)
    logger.info = MagicMock()

    return ManageFixedItemsUseCase(
        fixed_item_repo=fixed_item_repo,
        fixed_item_history_repo=history_repo,
        logger=logger,
    )


async def test_same_month_correction_overwrites() -> None:
    """同じ適用開始年月で登録し直すと、行が増えず金額が置き換わる"""
    repo = FakeFixedItemHistoryRepository()
    usecase = _build_usecase(repo)

    await usecase.add_fixed_item_history(
        AddFixedItemHistoryCommand(fixed_item_id=1, year=2026, month=5, amount=60000)
    )
    await usecase.add_fixed_item_history(
        AddFixedItemHistoryCommand(fixed_item_id=1, year=2026, month=5, amount=60440)
    )

    assert len(repo.histories) == 1
    assert repo.histories[0].amount == Money(60440)


async def test_correction_after_end_operation_takes_effect() -> None:
    """運用終了と同じ年月に金額を入れ直すと、終了が取り消されて金額が有効になる

    これがマイグレーション009以前に黙って無視されていたケース。
    """
    repo = FakeFixedItemHistoryRepository()
    usecase = _build_usecase(repo)

    await usecase.end_fixed_item_operation(
        EndFixedItemOperationCommand(fixed_item_id=1, year=2026, month=5)
    )
    await usecase.add_fixed_item_history(
        AddFixedItemHistoryCommand(fixed_item_id=1, year=2026, month=5, amount=60440)
    )

    assert len(repo.histories) == 1

    active = await usecase.get_active_fixed_items_at(2026, 8)
    assert len(active) == 1
    assert active[0].amount == Money(60440)


async def test_end_operation_after_registration_takes_effect() -> None:
    """金額登録と同じ年月に運用終了を入れると、終了が反映される"""
    repo = FakeFixedItemHistoryRepository()
    usecase = _build_usecase(repo)

    await usecase.add_fixed_item_history(
        AddFixedItemHistoryCommand(fixed_item_id=1, year=2026, month=5, amount=60440)
    )
    await usecase.end_fixed_item_operation(
        EndFixedItemOperationCommand(fixed_item_id=1, year=2026, month=5)
    )

    assert len(repo.histories) == 1
    assert repo.histories[0].is_deleted()

    active = await usecase.get_active_fixed_items_at(2026, 8)
    assert active == []


async def test_different_months_are_kept_separately() -> None:
    """適用開始年月が違えば別の履歴として残る（改定は上書きしない）"""
    repo = FakeFixedItemHistoryRepository()
    usecase = _build_usecase(repo)

    await usecase.add_fixed_item_history(
        AddFixedItemHistoryCommand(fixed_item_id=1, year=2025, month=4, amount=40000)
    )
    await usecase.add_fixed_item_history(
        AddFixedItemHistoryCommand(fixed_item_id=1, year=2026, month=5, amount=60440)
    )

    assert len(repo.histories) == 2
    fixed_expenses = FixedExpenses(await repo.find_active_at(YearMonth(2026, 8)))
    assert fixed_expenses.calculate() == Money(60440)
