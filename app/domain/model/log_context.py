"""ログコンテキストのドメインモデル"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class LogContext:
    """ログに含めるコンテキスト情報"""

    screen: str | None = None
    """画面識別子（dashboard, month, settings等）"""
    context: dict[str, Any] | None = None
    """追加コンテキスト情報（year, month, card_id等）"""

    def to_dict(self) -> dict[str, Any]:
        """辞書形式に変換"""
        result: dict[str, Any] = {}
        if self.screen:
            result["screen"] = self.screen
        if self.context:
            result.update(self.context)
        return result
