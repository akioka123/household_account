"""カードのSQLAlchemyモデル"""
from __future__ import annotations

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.database import Base


class CardModel(Base):
    """カードテーブルのSQLAlchemyモデル"""

    __tablename__ = "cards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    """カード名"""
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    """有効フラグ"""
