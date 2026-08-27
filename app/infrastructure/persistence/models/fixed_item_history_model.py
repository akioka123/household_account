"""固定費履歴のSQLAlchemyモデル"""
from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.database import Base


class FixedItemHistoryModel(Base):
    """固定費履歴テーブルのSQLAlchemyモデル"""

    __tablename__ = "fixed_item_histories"
    __table_args__ = (
        # 同一項目・同一適用開始年月の金額は1つに定まる（同月内の訂正は上書き）
        UniqueConstraint(
            "fixed_item_id",
            "effective_from",
            name="uq_fixed_item_histories_item_effective_from",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fixed_item_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("fixed_items.id"), nullable=False, index=True
    )
    """固定費項目ID"""
    effective_from: Mapped[str] = mapped_column(String(7), nullable=False, index=True)
    """適用開始年月（YYYY-MM形式）"""
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    """金額"""
    card_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("cards.id"), nullable=True
    )
    """カード紐づけ（任意）"""
    included_in_card: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    """カード請求に含まれる固定費かどうか"""

