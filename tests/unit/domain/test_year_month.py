"""YearMonthのテスト"""
from __future__ import annotations

import pytest

from app.domain.model.year_month import YearMonth


def test_year_month_creation() -> None:
    """YearMonthの作成"""
    ym = YearMonth(2024, 5)
    assert ym.year == 2024
    assert ym.month == 5


def test_year_month_invalid_year() -> None:
    """無効な年の場合、例外を発生"""
    with pytest.raises(ValueError, match="year out of range"):
        YearMonth(1899, 1)
    
    with pytest.raises(ValueError, match="year out of range"):
        YearMonth(10000, 1)


def test_year_month_invalid_month() -> None:
    """無効な月の場合、例外を発生"""
    with pytest.raises(ValueError, match="month out of range"):
        YearMonth(2024, 0)
    
    with pytest.raises(ValueError, match="month out of range"):
        YearMonth(2024, 13)


def test_year_month_next_month() -> None:
    """次の月を取得"""
    ym1 = YearMonth(2024, 5)
    ym2 = ym1.next_month()
    assert ym2.year == 2024
    assert ym2.month == 6


def test_year_month_next_month_year_rollover() -> None:
    """12月の次の月は翌年1月"""
    ym1 = YearMonth(2024, 12)
    ym2 = ym1.next_month()
    assert ym2.year == 2025
    assert ym2.month == 1


def test_year_month_to_string() -> None:
    """YYYY-MM形式の文字列に変換"""
    ym = YearMonth(2024, 5)
    assert str(ym) == "YearMonth(year=2024, month=5)"


def test_year_month_comparison() -> None:
    """YearMonthの比較（順序）"""
    ym1 = YearMonth(2024, 5)
    ym2 = YearMonth(2024, 6)
    ym3 = YearMonth(2025, 1)
    
    assert ym1 < ym2
    assert ym2 < ym3
    assert ym1 < ym3
