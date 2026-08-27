"""固定費の集約（算出処理を含む）"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.model.fixed_item_history import FixedItemHistory
from app.domain.model.money import Money


@dataclass(frozen=True)
class FixedExpenses:
    """固定費の集約（固定費合計とカードIDごとの固定費合計）"""

    histories: list[FixedItemHistory]

    def calculate(self) -> Money:
        """固定費履歴のリストから固定費を算出

        算出ルール:
            - 削除済み（is_deleted()）の履歴は除外
            - 同じfixed_item_idで複数の履歴がある場合、effective_fromが最新のものを採用
            - 固定費合計を計算
        """
        fixed_total = Money(0)
        for history in self._latest_active_histories():
            fixed_total = fixed_total + history.amount
        return fixed_total

    def by_card(self) -> dict[int, Money]:
        """カードIDごとの固定費合計を取得（項目ごとに最新の有効な履歴のみを対象）"""
        fixed_in_card_by_card: dict[int, Money] = {}

        for history in self._latest_active_histories():
            if history.included_in_card and history.card_id:
                card_id = history.card_id
                if card_id not in fixed_in_card_by_card:
                    fixed_in_card_by_card[card_id] = Money(0)
                fixed_in_card_by_card[card_id] = fixed_in_card_by_card[card_id] + history.amount

        return fixed_in_card_by_card

    def _latest_active_histories(self) -> list[FixedItemHistory]:
        """項目ごとに最新の履歴を選び、削除済み（金額0）を除いたもの"""
        return [h for h in self.get_effective_histories() if not h.is_deleted()]

    def get_effective_histories(self) -> list[FixedItemHistory]:
        """有効な固定費履歴を取得"""
        effective_histories: list[FixedItemHistory] = []

        for history in self.histories:
            if history.fixed_item_id not in [h.fixed_item_id for h in effective_histories]:
                effective_histories.append(history)
            elif (
                history.effective_from
                > [
                    h.effective_from
                    for h in effective_histories
                    if h.fixed_item_id == history.fixed_item_id
                ][0]
            ):
                effective_histories = list(
                    filter(lambda h: h.fixed_item_id != history.fixed_item_id, effective_histories)
                )
                effective_histories.append(history)

        return effective_histories
