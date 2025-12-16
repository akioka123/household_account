"""固定費管理ユースケース"""
from __future__ import annotations

from dataclasses import dataclass

from app.application.port.fixed_item_history_repository import FixedItemHistoryRepository
from app.application.port.fixed_item_repository import FixedItemRepository
from app.application.port.logger import Logger
from app.domain.model.fixed_item import FixedItem
from app.domain.model.fixed_item_history import FixedItemHistory
from app.domain.model.log_context import LogContext
from app.domain.model.money import Money
from app.domain.model.year_month import YearMonth


@dataclass(frozen=True)
class AddFixedItemCommand:
    """固定費項目追加コマンド"""

    name: str
    """項目名"""


@dataclass(frozen=True)
class AddFixedItemHistoryCommand:
    """固定費履歴追加コマンド"""

    fixed_item_id: int
    """固定費項目ID"""
    year: int
    """適用開始年"""
    month: int
    """適用開始月"""
    amount: int
    """金額"""
    card_id: int | None = None
    """カード紐づけ（任意）"""
    included_in_card: bool = False
    """カード請求に含まれる固定費かどうか"""


@dataclass(frozen=True)
class ActiveFixedItem:
    """有効な固定費（表示用）"""

    fixed_item_id: int
    """固定費項目ID"""
    name: str
    """項目名"""
    effective_from: YearMonth
    """適用開始年月"""
    amount: Money
    """金額"""
    card_id: int | None
    """カード紐づけ"""
    included_in_card: bool
    """カード請求に含まれる固定費かどうか"""


class ManageFixedItemsUseCase:
    """固定費管理ユースケース"""

    def __init__(
        self,
        fixed_item_repo: FixedItemRepository,
        fixed_item_history_repo: FixedItemHistoryRepository,
        logger: Logger,
    ) -> None:
        self._fixed_item_repo = fixed_item_repo
        self._fixed_item_history_repo = fixed_item_history_repo
        self._logger = logger

    async def add_fixed_item(self, command: AddFixedItemCommand) -> FixedItem:
        """固定費項目を追加

        Args:
            command: 固定費項目追加コマンド

        Returns:
            作成された固定費項目
        """
        # 最大IDを取得して次のIDを決定（簡易実装）
        all_items = await self._fixed_item_repo.find_all()
        next_id = max([item.id for item in all_items], default=0) + 1

        fixed_item = FixedItem(id=next_id, name=command.name)
        await self._fixed_item_repo.save(fixed_item)

        context = LogContext(
            screen="month", context={"fixed_item_id": fixed_item.id, "action": "add_fixed_item"}
        )
        self._logger.info(f"固定費項目追加: {fixed_item.name}", context)

        return fixed_item

    async def add_fixed_item_history(self, command: AddFixedItemHistoryCommand) -> None:
        """固定費履歴を追加

        Args:
            command: 固定費履歴追加コマンド

        Raises:
            ValueError: 固定費項目が見つからない場合
        """
        # 固定費項目の存在確認
        fixed_item = await self._fixed_item_repo.find_by_id(command.fixed_item_id)
        if fixed_item is None:
            raise ValueError(f"FixedItem not found: {command.fixed_item_id}")

        # 最大IDを取得して次のIDを決定（全データから取得してグローバルな一意性を保証）
        all_histories = await self._fixed_item_history_repo.find_all()
        next_id = max([h.id for h in all_histories], default=0) + 1

        effective_from = YearMonth(command.year, command.month)
        history = FixedItemHistory(
            id=next_id,
            fixed_item_id=command.fixed_item_id,
            effective_from=effective_from,
            amount=Money(command.amount),
            card_id=command.card_id,
            included_in_card=command.included_in_card,
        )

        await self._fixed_item_history_repo.save(history)

        context = LogContext(
            screen="month",
            context={
                "fixed_item_id": command.fixed_item_id,
                "year": command.year,
                "month": command.month,
                "action": "add_fixed_item_history",
            },
        )
        self._logger.info(
            f"固定費履歴追加: {fixed_item.name} ({command.year}年{command.month}月)",
            context,
        )

    async def get_active_fixed_items_at(self, year: int, month: int) -> list[ActiveFixedItem]:
        """指定年月で有効な固定費を取得

        Args:
            year: 年
            month: 月

        Returns:
            有効な固定費のリスト
        """
        ym = YearMonth(year, month)

        # 指定年月で有効な履歴を取得
        histories = await self._fixed_item_history_repo.find_active_at(ym)

        # 各履歴について、固定費項目情報を取得
        result: list[ActiveFixedItem] = []
        for history in histories:
            # 削除済み（金額0）の場合はスキップ
            if history.is_deleted():
                continue

            fixed_item = await self._fixed_item_repo.find_by_id(history.fixed_item_id)
            if fixed_item is None:
                continue

            # 同じ固定費項目で複数の履歴がある場合、最新のものを採用
            # （effective_fromが最大のもの）
            existing = next(
                (r for r in result if r.fixed_item_id == history.fixed_item_id), None
            )
            if existing is None or history.effective_from > existing.effective_from:
                if existing:
                    result.remove(existing)
                result.append(
                    ActiveFixedItem(
                        fixed_item_id=fixed_item.id,
                        name=fixed_item.name,
                        effective_from=history.effective_from,
                        amount=history.amount,
                        card_id=history.card_id,
                        included_in_card=history.included_in_card,
                    )
                )

        return result

    async def get_all_fixed_items(self) -> list[FixedItem]:
        """全固定費項目を取得

        Returns:
            全固定費項目のリスト
        """
        return await self._fixed_item_repo.find_all()

