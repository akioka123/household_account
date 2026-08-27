"""引出明細のSQLAlchemy実装"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.model.withdrawal import Withdrawal
from app.domain.model.year_month import YearMonth
from app.infrastructure.persistence.models.withdrawal_model import WithdrawalModel


class SqlAlchemyWithdrawalRepository:
    """引出明細のSQLAlchemy実装"""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_year_month(self, ym: YearMonth) -> list[Withdrawal]:
        """指定年月の引出明細を取得（日付順）"""
        ym_str = f"{ym.year:04d}-{ym.month:02d}"
        stmt = (
            select(WithdrawalModel)
            .where(WithdrawalModel.year_month == ym_str)
            .order_by(WithdrawalModel.withdrawal_date)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return [self._to_domain(model) for model in models]

    async def find_all(self) -> list[Withdrawal]:
        """全引出明細を取得"""
        stmt = select(WithdrawalModel).order_by(WithdrawalModel.id)
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return [self._to_domain(model) for model in models]

    async def save(self, withdrawal: Withdrawal) -> None:
        """引出明細を保存（新規作成または更新）"""
        ym_str = f"{withdrawal.year_month.year:04d}-{withdrawal.year_month.month:02d}"
        stmt = select(WithdrawalModel).where(WithdrawalModel.id == withdrawal.id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            # 更新
            model.year_month = ym_str
            model.withdrawal_date = withdrawal.withdrawal_date
            model.amount = withdrawal.amount.amount
            model.note = withdrawal.note
        else:
            # 新規作成
            model = WithdrawalModel(
                id=withdrawal.id,
                year_month=ym_str,
                withdrawal_date=withdrawal.withdrawal_date,
                amount=withdrawal.amount.amount,
                note=withdrawal.note,
            )
            self._session.add(model)

        await self._session.flush()

    async def delete(self, withdrawal_id: int) -> None:
        """引出明細を削除"""
        stmt = select(WithdrawalModel).where(WithdrawalModel.id == withdrawal_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            await self._session.delete(model)
            await self._session.flush()

    def _to_domain(self, model: WithdrawalModel) -> Withdrawal:
        """SQLAlchemyモデルをドメインモデルに変換"""
        from app.domain.model.money import Money

        # year_monthをYearMonthに変換
        year, month = map(int, model.year_month.split("-"))
        year_month = YearMonth(year, month)

        return Withdrawal(
            id=model.id,
            year_month=year_month,
            withdrawal_date=model.withdrawal_date,
            amount=Money(model.amount),
            note=model.note,
        )
