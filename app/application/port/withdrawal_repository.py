"""引出明細の永続化Port"""
from __future__ import annotations

from typing import Protocol

from app.domain.model.withdrawal import Withdrawal
from app.domain.model.year_month import YearMonth


class WithdrawalRepository(Protocol):
    """引出明細の永続化Port"""

    async def find_by_year_month(self, ym: YearMonth) -> list[Withdrawal]:
        """指定年月の引出明細を取得（日付順）"""
        ...

    async def find_all(self) -> list[Withdrawal]:
        """全引出明細を取得"""
        ...

    async def save(self, withdrawal: Withdrawal) -> None:
        """引出明細を保存（新規作成または更新）"""
        ...

    async def delete(self, withdrawal_id: int) -> None:
        """引出明細を削除"""
        ...
