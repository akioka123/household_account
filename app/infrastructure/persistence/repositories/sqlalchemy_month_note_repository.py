"""月次メモのSQLAlchemy実装"""
from __future__ import annotations

from sqlalchemy import delete as sa_delete
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.model.month_note import MonthNote
from app.domain.model.year_month import YearMonth
from app.infrastructure.persistence.models.month_note_model import MonthNoteModel


class SqlAlchemyMonthNoteRepository:
    """月次メモのSQLAlchemy実装"""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find(self, ym: YearMonth) -> MonthNote | None:
        """指定年月の月次メモを取得"""
        stmt = select(MonthNoteModel).where(MonthNoteModel.year_month == ym.to_string())
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            return None

        return self._to_domain(model)

    async def find_by_year(self, year: int) -> dict[YearMonth, MonthNote]:
        """指定年の月次メモを年月をキーにして取得"""
        stmt = (
            select(MonthNoteModel)
            .where(MonthNoteModel.year_month.like(f"{year:04d}-%"))
            .order_by(MonthNoteModel.year_month)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        notes: dict[YearMonth, MonthNote] = {}
        for model in models:
            note = self._to_domain(model)
            notes[note.year_month] = note
        return notes

    async def save(self, note: MonthNote) -> None:
        """月次メモを保存（新規作成または更新）"""
        ym_str = note.year_month.to_string()
        stmt = select(MonthNoteModel).where(MonthNoteModel.year_month == ym_str)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            # 更新
            model.note = note.note
        else:
            # 新規作成
            model = MonthNoteModel(year_month=ym_str, note=note.note)
            self._session.add(model)

        await self._session.flush()

    async def delete(self, ym: YearMonth) -> None:
        """指定年月の月次メモを削除"""
        stmt = sa_delete(MonthNoteModel).where(MonthNoteModel.year_month == ym.to_string())
        await self._session.execute(stmt)
        await self._session.flush()

    def _to_domain(self, model: MonthNoteModel) -> MonthNote:
        """SQLAlchemyモデルをドメインモデルに変換"""
        return MonthNote(
            id=model.id,
            year_month=YearMonth.from_string(model.year_month),
            note=model.note,
        )
