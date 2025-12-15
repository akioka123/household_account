from __future__ import annotations

from fastapi import APIRouter, Depends, Form
from fastapi.responses import HTMLResponse

from app.application.usecase.register_income import (
    RegisterIncomeCommand,
    RegisterIncomeUseCase,
)
from app.application.port.income_repository import IncomeRepository
from app.infrastructure.persistence.inmemory.income_repository import InMemoryIncomeRepository

router = APIRouter()


# NOTE: 実運用では SQLite Adapter に差し替える（Port/Adapterの差し替え点）
def provide_income_repo() -> IncomeRepository:
    return InMemoryIncomeRepository()


def provide_register_income_uc(
    repo: IncomeRepository = Depends(provide_income_repo),
) -> RegisterIncomeUseCase:
    return RegisterIncomeUseCase(income_repo=repo)


@router.get("/month/{year}/{month}", response_class=HTMLResponse)
def month_page(year: int, month: int) -> str:
    # NOTE: 本来はテンプレート/Jinja2。サンプルは最小HTMLのみ。
    return f"""<html><body>
<h1>{year}-{month:02d}</h1>
<form hx-post="/month/{year}/{month}/income" hx-target="#result" hx-swap="innerHTML">
  <input type="number" name="salary_gross" placeholder="salary_gross" />
  <input type="number" name="salary_net" placeholder="salary_net" />
  <input type="number" name="bonus_gross" placeholder="bonus_gross" />
  <input type="number" name="bonus_net" placeholder="bonus_net" />
  <button type="submit">save</button>
</form>
<div id="result"></div>
</body></html>"""


@router.post("/month/{year}/{month}/income", response_class=HTMLResponse)
def register_income(
    year: int,
    month: int,
    salary_gross: int = Form(...),
    salary_net: int = Form(...),
    bonus_gross: int = Form(0),
    bonus_net: int = Form(0),
    uc: RegisterIncomeUseCase = Depends(provide_register_income_uc),
) -> str:
    cmd = RegisterIncomeCommand(
        year=year,
        month=month,
        salary_gross=salary_gross,
        salary_net=salary_net,
        bonus_gross=bonus_gross,
        bonus_net=bonus_net,
    )
    uc.execute(cmd)
    return "<p>saved</p>"
