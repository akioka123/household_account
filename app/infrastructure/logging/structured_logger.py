"""構造化ログ実装"""
from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from app.application.port.logger import Logger
from app.domain.model.log_context import LogContext


class StructuredLogger:
    """構造化ログを標準出力に出力するLogger実装"""

    def __init__(self, name: str, request_id: UUID | None = None) -> None:
        self._name = name
        self._request_id = request_id
        self._logger = logging.getLogger(name)

    def _log(
        self,
        level: str,
        message: str,
        context: LogContext | None = None,
    ) -> None:
        """ログを構造化形式で出力"""
        log_data: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "logger": self._name,
            "message": message,
        }

        if self._request_id:
            log_data["request_id"] = str(self._request_id)

        if context:
            context_dict = context.to_dict()
            if context_dict:
                log_data.update(context_dict)

        # JSON形式で標準出力に出力（Docker対応）
        print(json.dumps(log_data, ensure_ascii=False), file=sys.stdout, flush=True)

    def debug(self, message: str, context: LogContext | None = None) -> None:
        """DEBUGレベルのログを出力"""
        self._log("DEBUG", message, context)

    def info(self, message: str, context: LogContext | None = None) -> None:
        """INFOレベルのログを出力"""
        self._log("INFO", message, context)

    def warning(self, message: str, context: LogContext | None = None) -> None:
        """WARNINGレベルのログを出力"""
        self._log("WARNING", message, context)

    def error(self, message: str, context: LogContext | None = None) -> None:
        """ERRORレベルのログを出力"""
        self._log("ERROR", message, context)


def create_logger(name: str, request_id: UUID | None = None) -> Logger:
    """Loggerインスタンスを作成"""
    return StructuredLogger(name, request_id)
