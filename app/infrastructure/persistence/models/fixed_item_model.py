"""固定費項目のSQLAlchemyモデル"""
from __future__ import annotations

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.database import Base


class FixedItemModel(Base):
    """固定費項目テーブルのSQLAlchemyモデル"""

    __tablename__ = "fixed_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    """項目名"""

