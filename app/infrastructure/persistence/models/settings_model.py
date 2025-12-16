"""設定のSQLAlchemyモデル"""
from __future__ import annotations

from sqlalchemy import Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.database import Base


class SettingsModel(Base):
    """設定テーブルのSQLAlchemyモデル（シングルトン）"""

    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    """設定ID（常に1）"""
    max_variable_items: Mapped[int] = mapped_column(Integer, nullable=False, default=20)
    """変動費最大件数"""
    max_fixed_items: Mapped[int] = mapped_column(Integer, nullable=False, default=20)
    """固定費最大件数"""

