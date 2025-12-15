"""ロガーのPort（Protocol）"""
from __future__ import annotations

from typing import Protocol

from app.domain.model.log_context import LogContext


class Logger(Protocol):
    """ロガーのProtocol。application層はこのProtocolのみに依存する"""

    def debug(self, message: str, context: LogContext | None = None) -> None:
        """DEBUGレベルのログを出力"""
        ...

    def info(self, message: str, context: LogContext | None = None) -> None:
        """INFOレベルのログを出力"""
        ...

    def warning(self, message: str, context: LogContext | None = None) -> None:
        """WARNINGレベルのログを出力"""
        ...

    def error(self, message: str, context: LogContext | None = None) -> None:
        """ERRORレベルのログを出力"""
        ...
