"""月初現金のSQLAlchemyモデル"""
from __future__ import annotations

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.database import Base


class CashBalanceModel(Base):
    """月初現金テーブルのSQLAlchemyモデル"""

    __tablename__ = "cash_balances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    year_month: Mapped[str] = mapped_column(String(7), nullable=False, unique=True, index=True)
    """対象年月（YYYY-MM形式）"""
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    """月初現金"""
