"""設定のエンティティ"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """アプリケーション設定"""

    max_variable_items: int
    """変動費最大件数"""
    max_fixed_items: int
    """固定費最大件数"""

    def __post_init__(self) -> None:
        """不変条件の検証"""
        if self.max_variable_items < 1:
            raise ValueError("max_variable_items must be >= 1")
        if self.max_fixed_items < 1:
            raise ValueError("max_fixed_items must be >= 1")

    @staticmethod
    def default() -> Settings:
        """デフォルト設定を取得"""
        return Settings(max_variable_items=20, max_fixed_items=20)

    def update_limits(
        self,
        max_variable_items: int | None = None,
        max_fixed_items: int | None = None,
    ) -> Settings:
        """上限設定を更新（新しいインスタンスを返す）"""
        return Settings(
            max_variable_items=max_variable_items or self.max_variable_items,
            max_fixed_items=max_fixed_items or self.max_fixed_items,
        )
