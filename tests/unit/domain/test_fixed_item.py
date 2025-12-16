"""FixedItemのテスト"""
from __future__ import annotations

from app.domain.model.fixed_item import FixedItem


def test_fixed_item_creation() -> None:
    """FixedItemの作成"""
    item = FixedItem(id=1, name="家賃")
    assert item.id == 1
    assert item.name == "家賃"


def test_fixed_item_rename() -> None:
    """FixedItemの名前変更"""
    item = FixedItem(id=1, name="家賃")
    renamed = item.rename("月額家賃")
    assert renamed.id == 1
    assert renamed.name == "月額家賃"
    # 元のインスタンスは変更されない（immutable）
    assert item.name == "家賃"

