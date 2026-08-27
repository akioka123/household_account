import pytest

from app.domain.model.year_month import YearMonth


def test_should_create_next_month_when_december():
    ym = YearMonth(2026, 12)
    assert ym.next_month() == YearMonth(2027, 1)


def test_should_raise_when_month_out_of_range():
    with pytest.raises(ValueError):
        YearMonth(2026, 13)
