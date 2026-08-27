"""LivingExpenseItemのテスト"""
from __future__ import annotations

import pytest

from app.domain.model.living_expense_item import (
    LIVING_EXPENSE_ITEM_SUBCATEGORY_DAILY_GOODS,
    LIVING_EXPENSE_ITEM_SUBCATEGORY_GROCERY,
    LivingExpenseItem,
)
from app.domain.model.money import Money


def test_living_expense_item_creation() -> None:
    """有効な値でインスタンス化できる"""
    item = LivingExpenseItem(
        id=1,
        living_expense_id=10,
        name="牛乳",
        amount=Money(200),
        sub_category=LIVING_EXPENSE_ITEM_SUBCATEGORY_GROCERY,
    )
    assert item.id == 1
    assert item.living_expense_id == 10
    assert item.name == "牛乳"
    assert item.amount.amount == 200
    assert item.sub_category == LIVING_EXPENSE_ITEM_SUBCATEGORY_GROCERY


def test_living_expense_item_allows_zero_amount() -> None:
    """金額0円は境界値として許可される"""
    item = LivingExpenseItem(
        id=1,
        living_expense_id=10,
        name="試供品",
        amount=Money(0),
        sub_category=LIVING_EXPENSE_ITEM_SUBCATEGORY_DAILY_GOODS,
    )
    assert item.amount.amount == 0


def test_living_expense_item_negative_amount_raises() -> None:
    """金額が負の場合は例外になる"""
    with pytest.raises(ValueError, match="金額は0以上の整数で入力してください"):
        LivingExpenseItem(
            id=1,
            living_expense_id=10,
            name="牛乳",
            amount=Money(-1),
            sub_category=LIVING_EXPENSE_ITEM_SUBCATEGORY_GROCERY,
        )


def test_living_expense_item_empty_name_raises() -> None:
    """品目名が空文字の場合は例外になる"""
    with pytest.raises(ValueError, match="品目名を入力してください"):
        LivingExpenseItem(
            id=1,
            living_expense_id=10,
            name="",
            amount=Money(200),
            sub_category=LIVING_EXPENSE_ITEM_SUBCATEGORY_GROCERY,
        )


def test_living_expense_item_blank_name_raises() -> None:
    """品目名が空白のみの場合は例外になる"""
    with pytest.raises(ValueError, match="品目名を入力してください"):
        LivingExpenseItem(
            id=1,
            living_expense_id=10,
            name="   ",
            amount=Money(200),
            sub_category=LIVING_EXPENSE_ITEM_SUBCATEGORY_GROCERY,
        )


def test_living_expense_item_invalid_sub_category_raises() -> None:
    """小分類が固定リストに含まれない場合は例外になる（実装がバリデーションしているため）"""
    with pytest.raises(ValueError, match="小分類は食品または生活用品のいずれかを指定してください"):
        LivingExpenseItem(
            id=1,
            living_expense_id=10,
            name="牛乳",
            amount=Money(200),
            sub_category="unknown",
        )
