"""構造化ロガーのテスト"""
from __future__ import annotations

import json
from uuid import uuid4

import pytest

from app.domain.model.log_context import LogContext
from app.infrastructure.logging.structured_logger import StructuredLogger


def test_log_info_without_context(capsys: pytest.CaptureFixture[str]) -> None:
    """コンテキストなしでINFOログを出力"""
    logger = StructuredLogger("test")
    logger.info("Test message")

    captured = capsys.readouterr()
    log_data = json.loads(captured.out.strip())

    assert log_data["level"] == "INFO"
    assert log_data["logger"] == "test"
    assert log_data["message"] == "Test message"
    assert "timestamp" in log_data


def test_log_with_request_id(capsys: pytest.CaptureFixture[str]) -> None:
    """request_id付きでログを出力"""
    request_id = uuid4()
    logger = StructuredLogger("test", request_id)
    logger.info("Test message")

    captured = capsys.readouterr()
    log_data = json.loads(captured.out.strip())

    assert log_data["request_id"] == str(request_id)


def test_log_with_context(capsys: pytest.CaptureFixture[str]) -> None:
    """コンテキスト付きでログを出力"""
    logger = StructuredLogger("test")
    context = LogContext(screen="dashboard", context={"year": 2024})
    logger.info("Test message", context)

    captured = capsys.readouterr()
    log_data = json.loads(captured.out.strip())

    assert log_data["screen"] == "dashboard"
    assert log_data["year"] == 2024


def test_log_all_levels(capsys: pytest.CaptureFixture[str]) -> None:
    """すべてのログレベルをテスト"""
    logger = StructuredLogger("test")

    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")

    captured = capsys.readouterr()
    lines = captured.out.strip().split("\n")

    assert len(lines) == 4
    levels = [json.loads(line)["level"] for line in lines]
    assert "DEBUG" in levels
    assert "INFO" in levels
    assert "WARNING" in levels
    assert "ERROR" in levels
