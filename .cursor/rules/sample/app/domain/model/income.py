from __future__ import annotations

from dataclasses import dataclass

from app.domain.model.money import Money


@dataclass(frozen=True)
class Income:
    """当月の収入（給与/賞与）。"""
    salary_gross: Money
    salary_net: Money
    bonus_gross: Money
    bonus_net: Money

    @staticmethod
    def of(
        salary_gross: int,
        salary_net: int,
        bonus_gross: int,
        bonus_net: int,
    ) -> "Income":
        return Income(
            salary_gross=Money(salary_gross),
            salary_net=Money(salary_net),
            bonus_gross=Money(bonus_gross),
            bonus_net=Money(bonus_net),
        )

    def net_total(self) -> Money:
        return self.salary_net + self.bonus_net
