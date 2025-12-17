"""固定費の集約（算出処理を含む）"""
from __future__ import annotations

from dataclasses import dataclass

from app.domain.model.fixed_item_history import FixedItemHistory
from app.domain.model.money import Money


@dataclass(frozen=True)
class FixedExpenses:
    """固定費の集約（固定費合計とカードIDごとの固定費合計）"""

    total: Money
    """固定費合計"""
    by_card: dict[int, Money]
    """カードIDごとの固定費合計"""

    @staticmethod
    def calculate(histories: list[FixedItemHistory]) -> FixedExpenses:
        """固定費履歴のリストから固定費を算出
        
        Args:
            histories: 固定費履歴のリスト
            
        Returns:
            固定費の集約
            
        算出ルール:
            - 削除済み（is_deleted()）の履歴は除外
            - 同じfixed_item_idで複数の履歴がある場合、effective_fromが最新のものを採用
            - 固定費合計を計算
            - included_in_cardがTrueかつcard_idが設定されている場合、カードIDごとの合計も計算
        """
        # まず、各fixed_item_idで最新の履歴を選ぶ
        latest_by_item_id: dict[int, FixedItemHistory] = {}
        for history in histories:
            if history.is_deleted():
                continue

            item_id = history.fixed_item_id
            if item_id not in latest_by_item_id:
                latest_by_item_id[item_id] = history
            elif history.effective_from > latest_by_item_id[item_id].effective_from:
                latest_by_item_id[item_id] = history

        # 最新の履歴のみを使って固定費を集計
        fixed_total = Money(0)
        fixed_in_card_by_card: dict[int, Money] = {}  # カードIDごとの固定費合計

        for history in latest_by_item_id.values():
            fixed_total = fixed_total + history.amount

            # カードに含まれる固定費を集計
            if history.included_in_card and history.card_id:
                card_id = history.card_id
                if card_id not in fixed_in_card_by_card:
                    fixed_in_card_by_card[card_id] = Money(0)
                fixed_in_card_by_card[card_id] = (
                    fixed_in_card_by_card[card_id] + history.amount
                )

        return FixedExpenses(total=fixed_total, by_card=fixed_in_card_by_card)
