"""生活費のSQLAlchemyモデル"""
from __future__ import annotations

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.database import Base


class LivingExpenseModel(Base):
    """生活費テーブルのSQLAlchemyモデル"""

    __tablename__ = "living_expenses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    year_month: Mapped[str] = mapped_column(String(7), nullable=False, index=True)
    """対象年月（YYYY-MM形式）"""
    category: Mapped[str] = mapped_column(String(20), nullable=False)
    """カテゴリ"""
    location: Mapped[str | None] = mapped_column(String(20), nullable=True)
    """場所（食費以外は任意）"""
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    """金額"""
    note: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    """メモ"""
