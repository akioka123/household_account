"""月次メモのSQLAlchemyモデル"""
from __future__ import annotations

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.database import Base


class MonthNoteModel(Base):
    """月次メモテーブルのSQLAlchemyモデル"""

    __tablename__ = "month_notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    year_month: Mapped[str] = mapped_column(String(7), nullable=False, unique=True, index=True)
    """対象年月（YYYY-MM形式）"""
    note: Mapped[str] = mapped_column(Text, nullable=False)
    """メモ本文（当月の消費が平均以上／以下になった理由）"""
