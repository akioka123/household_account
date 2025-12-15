from app.application.usecase.register_income import (
    RegisterIncomeCommand,
    RegisterIncomeUseCase,
)
from app.domain.model.year_month import YearMonth
from app.infrastructure.persistence.inmemory.income_repository import InMemoryIncomeRepository


def test_should_upsert_income_when_execute():
    repo = InMemoryIncomeRepository()
    uc = RegisterIncomeUseCase(income_repo=repo)

    cmd = RegisterIncomeCommand(
        year=2026,
        month=2,
        salary_gross=300_000,
        salary_net=240_000,
        bonus_gross=0,
        bonus_net=0,
    )

    uc.execute(cmd)

    income = repo.find(YearMonth(2026, 2))
    assert income is not None
    assert income.salary_net.amount == 240_000
