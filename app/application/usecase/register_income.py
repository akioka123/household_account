"""収入登録ユースケース"""
from __future__ import annotations

from dataclasses import dataclass

from app.application.port.income_repository import IncomeRepository
from app.application.port.logger import Logger
from app.domain.model.income import Income
from app.domain.model.log_context import LogContext
from app.domain.model.year_month import YearMonth


@dataclass(frozen=True)
class RegisterIncomeCommand:
    """収入登録コマンド"""

    year: int
    """年"""
    month: int
    """月"""
    salary_gross: int
    """給与額面"""
    salary_net: int
    """給与手取り"""
    bonus_gross: int
    """賞与額面"""
    bonus_net: int
    """賞与手取り"""


class RegisterIncomeUseCase:
    """収入登録ユースケース"""

    def __init__(self, income_repo: IncomeRepository, logger: Logger) -> None:
        self._income_repo = income_repo
        self._logger = logger

    async def execute(self, command: RegisterIncomeCommand) -> None:
        """収入を登録または更新

        Args:
            command: 収入登録コマンド
        """
        ym = YearMonth(command.year, command.month)
        income = Income.of(
            salary_gross=command.salary_gross,
            salary_net=command.salary_net,
            bonus_gross=command.bonus_gross,
            bonus_net=command.bonus_net,
        )

        await self._income_repo.upsert(ym, income)

        # ログ出力
        context = LogContext(
            screen="month",
            context={"year": command.year, "month": command.month, "action": "register_income"},
        )
        self._logger.info(
            f"収入登録: {command.year}年{command.month}月", context
        )

