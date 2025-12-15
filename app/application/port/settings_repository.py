"""設定の永続化Port"""
from __future__ import annotations

from typing import Protocol

from app.domain.model.settings import Settings


class SettingsRepository(Protocol):
    """設定の永続化Port"""

    async def find() -> Settings:
        """設定を取得（存在しない場合はデフォルト設定を返す）"""
        ...

    async def save(self, settings: Settings) -> None:
        """設定を保存"""
        ...
