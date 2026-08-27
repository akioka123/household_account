"""レシート画像のファイルシステム保存（Port実装）"""
from __future__ import annotations

import io
from pathlib import Path

from PIL import Image, UnidentifiedImageError

# プロジェクトルート（このファイルから見て4階層上）配下の data/ を基準にレシート画像を保存する
_PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
_DATA_ROOT = _PROJECT_ROOT / "data"

# Pillowのフォーマット名 → 保存拡張子の対応（JPEG/PNGのみ対応、ADR-001）
_FORMAT_TO_EXTENSION = {
    "JPEG": "jpg",
    "PNG": "png",
}


class FilesystemReceiptImageStorage:
    """レシート画像をファイルシステム（data/receipts/）に保存するPort実装"""

    def __init__(self, data_root: Path | None = None) -> None:
        # data_root は "data/" ディレクトリ（相対パスの起点）。レシート画像はこの配下の receipts/ に保存する
        self._data_root = data_root if data_root is not None else _DATA_ROOT
        self._receipts_root = self._data_root / "receipts"

    async def validate_and_save(
        self, year: int, month: int, living_expense_id: int, data: bytes
    ) -> str:
        """画像データをPillowで検証し、ファイルシステムに保存する

        Raises:
            ValueError: 画像として読み込めない場合（保存は行わない）
        """
        extension = self._validate(data)

        ym_dir = f"{year:04d}-{month:02d}"
        target_dir = self._receipts_root / ym_dir
        target_dir.mkdir(parents=True, exist_ok=True)

        file_name = f"{living_expense_id}.{extension}"
        target_path = target_dir / file_name
        target_path.write_bytes(data)

        return f"receipts/{ym_dir}/{file_name}"

    async def delete(self, relative_path: str) -> None:
        """保存済み画像を削除する（存在しない場合は何もしない）"""
        # relative_path は "receipts/{YYYY-MM}/{id}.{ext}" 形式（data/ からの相対パス）
        target_path = self._data_root / relative_path
        if target_path.exists():
            target_path.unlink()

    def _validate(self, data: bytes) -> str:
        """画像データを検証し、保存拡張子（jpg/png）を返す

        Raises:
            ValueError: 空データ、またはPillowでデコードできない場合
        """
        if not data:
            raise ValueError(
                "画像を読み込めませんでした。JPEGまたはPNG形式のファイルを選択してください"
            )

        try:
            with Image.open(io.BytesIO(data)) as image:
                image.verify()
                image_format = image.format
        except (UnidentifiedImageError, OSError, ValueError):
            raise ValueError(
                "画像を読み込めませんでした。JPEGまたはPNG形式のファイルを選択してください"
            ) from None

        extension = _FORMAT_TO_EXTENSION.get(image_format or "")
        if extension is None:
            raise ValueError(
                "画像を読み込めませんでした。JPEGまたはPNG形式のファイルを選択してください"
            )

        return extension
