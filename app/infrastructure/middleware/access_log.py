"""アクセスログミドルウェア"""
from __future__ import annotations

import time
from uuid import UUID, uuid4

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.application.port.logger import Logger
from app.domain.model.log_context import LogContext
from app.infrastructure.logging.structured_logger import StructuredLogger


class AccessLogMiddleware(BaseHTTPMiddleware):
    """全HTTPリクエストをログに記録するミドルウェア"""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
        self._logger: Logger = StructuredLogger("access")

    async def dispatch(self, request: Request, call_next: ASGIApp) -> Response:
        """リクエストを処理し、アクセスログを出力"""
        # request_idを生成
        request_id = uuid4()
        request.state.request_id = request_id

        # リクエスト開始時刻
        start_time = time.time()

        # リクエスト処理
        try:
            response = await call_next(request)
        except Exception as e:
            # エラー発生時もログに記録
            elapsed_time = time.time() - start_time
            self._log_request(
                request,
                request_id,
                500,
                elapsed_time,
                error=str(e),
            )
            raise

        # レスポンス後、ログ出力
        elapsed_time = time.time() - start_time
        self._log_request(
            request,
            request_id,
            response.status_code,
            elapsed_time,
        )

        return response

    def _log_request(
        self,
        request: Request,
        request_id: UUID,
        status_code: int,
        elapsed_time: float,
        error: str | None = None,
    ) -> None:
        """アクセスログを出力"""
        context = LogContext(
            screen=self._extract_screen(request.url.path),
            context={
                "method": request.method,
                "path": request.url.path,
                "status_code": status_code,
                "elapsed_time_ms": round(elapsed_time * 1000, 2),
                "client_ip": request.client.host if request.client else None,
            },
        )

        logger = StructuredLogger("access", request_id)
        message = f"{request.method} {request.url.path} {status_code}"
        if error:
            logger.error(f"{message} - {error}", context)
        elif status_code >= 500:
            logger.error(message, context)
        elif status_code >= 400:
            logger.warning(message, context)
        else:
            logger.info(message, context)

    def _extract_screen(self, path: str) -> str | None:
        """パスから画面識別子を抽出"""
        if path.startswith("/dashboard"):
            return "dashboard"
        elif path.startswith("/month"):
            return "month"
        elif path.startswith("/settings"):
            return "settings"
        return None
