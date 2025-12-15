"""カード請求のSQLAlchemyモデル"""
from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.database import Base


class CardStatementModel(Base):
    """カード請求テーブルのSQLAlchemyモデル"""

    __tablename__ = "card_statements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    year_month: Mapped[str] = mapped_column(String(7), nullable=False, index=True)
    """対象年月（YYYY-MM形式）"""
    card_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("cards.id"), nullable=False, index=True
    )
    """カードID"""
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    """請求総額"""

    __table_args__ = (
        UniqueConstraint("year_month", "card_id", name="uq_card_statements_year_month_card"),
    )
