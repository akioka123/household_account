"""アクセスログミドルウェアの統合テスト"""
from __future__ import annotations

import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.infrastructure.middleware.access_log import AccessLogMiddleware


@pytest.fixture
def app_with_middleware() -> FastAPI:
    """ミドルウェア付きのFastAPIアプリを作成"""
    app = FastAPI()
    app.add_middleware(AccessLogMiddleware)

    @app.get("/test")
    def test_endpoint() -> dict[str, str]:
        return {"message": "ok"}

    @app.get("/error")
    def error_endpoint() -> None:
        raise ValueError("Test error")

    return app


def test_access_log_middleware_logs_request(
    app_with_middleware: FastAPI, capsys: pytest.CaptureFixture[str]
) -> None:
    """アクセスログミドルウェアがリクエストをログに記録する"""
    client = TestClient(app_with_middleware)
    response = client.get("/test")

    assert response.status_code == 200

    captured = capsys.readouterr()
    log_lines = [line for line in captured.out.strip().split("\n") if line.strip()]

    # アクセスログが出力されていることを確認
    access_logs = [
        json.loads(line) for line in log_lines if json.loads(line).get("logger") == "access"
    ]

    assert len(access_logs) > 0
    log_data = access_logs[0]
    assert log_data["method"] == "GET"
    assert log_data["path"] == "/test"
    assert log_data["status_code"] == 200
    assert "request_id" in log_data
    assert "elapsed_time_ms" in log_data


def test_access_log_middleware_extracts_screen(
    app_with_middleware: FastAPI, capsys: pytest.CaptureFixture[str]
) -> None:
    """アクセスログミドルウェアが画面識別子を抽出する"""
    client = TestClient(app_with_middleware)
    client.get("/dashboard/2024")
    client.get("/month/2024/5")
    client.get("/settings")

    captured = capsys.readouterr()
    log_lines = [line for line in captured.out.strip().split("\n") if line.strip()]

    access_logs = [
        json.loads(line) for line in log_lines if json.loads(line).get("logger") == "access"
    ]

    screens = [log.get("screen") for log in access_logs if log.get("screen")]
    assert "dashboard" in screens
    assert "month" in screens
    assert "settings" in screens
