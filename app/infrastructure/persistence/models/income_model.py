"""収入のSQLAlchemyモデル"""
from __future__ import annotations

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.database import Base


class IncomeModel(Base):
    """収入テーブルのSQLAlchemyモデル"""

    __tablename__ = "incomes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    year_month: Mapped[str] = mapped_column(String(7), nullable=False, unique=True, index=True)
    """YYYY-MM形式"""
    salary_gross: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    """給与額面"""
    salary_net: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    """給与手取り"""
    bonus_gross: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    """賞与額面"""
    bonus_net: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    """賞与手取り"""

