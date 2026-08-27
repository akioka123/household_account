from __future__ import annotations

from dataclasses import dataclass

from app.application.port.income_repository import IncomeRepository
from app.domain.model.year_month import YearMonth
from app.domain.model.income import Income


@dataclass(frozen=True)
class RegisterIncomeCommand:
    year: int
    month: int
    salary_gross: int
    salary_net: int
    bonus_gross: int
    bonus_net: int


class RegisterIncomeUseCase:
    """給与/賞与を登録するユースケース。

    参照：
    - Port定義 @../port/income_repository.py
    """

    def __init__(self, income_repo: IncomeRepository) -> None:
        self._income_repo = income_repo

    def execute(self, cmd: RegisterIncomeCommand) -> None:
        ym = YearMonth(cmd.year, cmd.month)
        income = Income.of(
            salary_gross=cmd.salary_gross,
            salary_net=cmd.salary_net,
            bonus_gross=cmd.bonus_gross,
            bonus_net=cmd.bonus_net,
        )
        self._income_repo.upsert(ym, income)
