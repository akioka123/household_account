"""Settingsのテスト"""
from __future__ import annotations

import pytest

from app.domain.model.settings import Settings


def test_settings_creation() -> None:
    """Settingsの作成"""
    settings = Settings(max_variable_items=20, max_fixed_items=30)
    assert settings.max_variable_items == 20
    assert settings.max_fixed_items == 30


def test_settings_invalid_max_variable_items() -> None:
    """無効なmax_variable_itemsの場合、例外を発生"""
    with pytest.raises(ValueError, match="max_variable_items must be >= 1"):
        Settings(max_variable_items=0, max_fixed_items=20)


def test_settings_invalid_max_fixed_items() -> None:
    """無効なmax_fixed_itemsの場合、例外を発生"""
    with pytest.raises(ValueError, match="max_fixed_items must be >= 1"):
        Settings(max_variable_items=20, max_fixed_items=0)


def test_settings_default() -> None:
    """デフォルト設定を取得"""
    settings = Settings.default()
    assert settings.max_variable_items == 20
    assert settings.max_fixed_items == 20


def test_settings_update_limits() -> None:
    """上限設定を更新"""
    settings = Settings.default()
    updated = settings.update_limits(max_variable_items=30)
    assert updated.max_variable_items == 30
    assert updated.max_fixed_items == 20

