"""レシート画像の永続化Port"""
from __future__ import annotations

from typing import Protocol


class ReceiptImageStoragePort(Protocol):
    """レシート画像の永続化Port"""

    async def validate_and_save(
        self, year: int, month: int, living_expense_id: int, data: bytes
    ) -> str:
        """画像データを検証して保存する

        Args:
            year: 対象年
            month: 対象月
            living_expense_id: 親レシート（LivingExpense）のID
            data: 画像バイナリデータ

        Returns:
            保存先の相対パス（data/receipts/ からの相対パス）

        Raises:
            ValueError: 画像として読み込めない場合
        """
        ...

    async def delete(self, relative_path: str) -> None:
        """保存済み画像を削除する"""
        ...
