"""Cardのテスト"""
from __future__ import annotations

from app.domain.model.card import Card


def test_card_creation() -> None:
    """Cardの作成"""
    card = Card(id=1, name="テストカード", enabled=True)
    assert card.id == 1
    assert card.name == "テストカード"
    assert card.enabled is True


def test_card_disable() -> None:
    """カードを無効化"""
    card = Card(id=1, name="テストカード", enabled=True)
    disabled = card.disable()
    assert disabled.enabled is False
    assert disabled.id == card.id
    assert disabled.name == card.name


def test_card_enable() -> None:
    """カードを有効化"""
    card = Card(id=1, name="テストカード", enabled=False)
    enabled = card.enable()
    assert enabled.enabled is True


def test_card_rename() -> None:
    """カード名を変更"""
    card = Card(id=1, name="テストカード", enabled=True)
    renamed = card.rename("新しいカード名")
    assert renamed.name == "新しいカード名"
    assert renamed.id == card.id
    assert renamed.enabled == card.enabled

