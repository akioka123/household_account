"""生活費品目のSQLAlchemyモデル"""
from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.database import Base


class LivingExpenseItemModel(Base):
    """生活費品目テーブルのSQLAlchemyモデル"""

    __tablename__ = "living_expense_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    living_expense_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("living_expenses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    """親レシート（living_expenses.id）"""
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    """品目名"""
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    """金額"""
    sub_category: Mapped[str] = mapped_column(String(20), nullable=False)
    """小分類（grocery / daily_goods）"""
