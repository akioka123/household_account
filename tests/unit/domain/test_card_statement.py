"""CardStatementのテスト"""
from __future__ import annotations

from app.domain.model.card_statement import CardStatement
from app.domain.model.money import Money
from app.domain.model.year_month import YearMonth


def test_card_statement_creation() -> None:
    """CardStatementの作成"""
    ym = YearMonth(2024, 3)
    statement = CardStatement(
        id=1,
        year_month=ym,
        card_id=2,
        amount=Money(50000),
    )
    assert statement.id == 1
    assert statement.year_month == ym
    assert statement.card_id == 2
    assert statement.amount.amount == 50000
