"""引出明細のSQLAlchemyモデル"""
from __future__ import annotations

from datetime import date

from sqlalchemy import Date, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.database import Base


class WithdrawalModel(Base):
    """引出明細テーブルのSQLAlchemyモデル"""

    __tablename__ = "withdrawals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    year_month: Mapped[str] = mapped_column(String(7), nullable=False, index=True)
    """対象年月（YYYY-MM形式）"""
    withdrawal_date: Mapped[date] = mapped_column(Date, nullable=False)
    """引出日付"""
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    """引出金額"""
    note: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    """メモ"""
