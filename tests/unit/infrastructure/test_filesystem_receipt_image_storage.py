"""FilesystemReceiptImageStorageのテスト（実ファイルシステムに対して検証する）"""
from __future__ import annotations

import io
from pathlib import Path

import pytest
from PIL import Image

from app.infrastructure.storage.filesystem_receipt_image_storage import (
    FilesystemReceiptImageStorage,
)


def _png_bytes() -> bytes:
    """テスト用の有効なPNGバイト列を生成する"""
    buffer = io.BytesIO()
    Image.new("RGB", (4, 4), color="red").save(buffer, format="PNG")
    return buffer.getvalue()


def _jpeg_bytes() -> bytes:
    """テスト用の有効なJPEGバイト列を生成する"""
    buffer = io.BytesIO()
    Image.new("RGB", (4, 4), color="blue").save(buffer, format="JPEG")
    return buffer.getvalue()


async def test_validate_and_save_stores_png_and_returns_relative_path(tmp_path: Path) -> None:
    """有効なPNGデータを保存すると相対パスが返り、実際にファイルが作成される"""
    storage = FilesystemReceiptImageStorage(data_root=tmp_path)

    relative_path = await storage.validate_and_save(2024, 3, 1, _png_bytes())

    assert relative_path == "receipts/2024-03/1.png"
    assert (tmp_path / relative_path).exists()


async def test_validate_and_save_stores_jpeg_and_returns_relative_path(tmp_path: Path) -> None:
    """有効なJPEGデータを保存すると相対パスが返り、実際にファイルが作成される"""
    storage = FilesystemReceiptImageStorage(data_root=tmp_path)

    relative_path = await storage.validate_and_save(2024, 3, 2, _jpeg_bytes())

    assert relative_path == "receipts/2024-03/2.jpg"
    assert (tmp_path / relative_path).exists()


async def test_validate_and_save_rejects_invalid_image_data(tmp_path: Path) -> None:
    """画像として読めないバイト列を渡すとValueErrorになり、ファイルは保存されない"""
    storage = FilesystemReceiptImageStorage(data_root=tmp_path)

    with pytest.raises(ValueError):
        await storage.validate_and_save(2024, 3, 3, b"not-an-image-data")

    receipts_dir = tmp_path / "receipts" / "2024-03"
    assert not receipts_dir.exists() or list(receipts_dir.iterdir()) == []


async def test_validate_and_save_rejects_empty_data(tmp_path: Path) -> None:
    """空データを渡すとValueErrorになる"""
    storage = FilesystemReceiptImageStorage(data_root=tmp_path)

    with pytest.raises(ValueError):
        await storage.validate_and_save(2024, 3, 4, b"")


async def test_delete_removes_saved_file(tmp_path: Path) -> None:
    """delete()で保存したファイルが削除される"""
    storage = FilesystemReceiptImageStorage(data_root=tmp_path)
    relative_path = await storage.validate_and_save(2024, 3, 1, _png_bytes())
    assert (tmp_path / relative_path).exists()

    await storage.delete(relative_path)

    assert not (tmp_path / relative_path).exists()


async def test_delete_does_nothing_when_file_not_found(tmp_path: Path) -> None:
    """存在しないファイルを指定してもdelete()は例外を発生させない"""
    storage = FilesystemReceiptImageStorage(data_root=tmp_path)

    await storage.delete("receipts/2024-03/999.png")
