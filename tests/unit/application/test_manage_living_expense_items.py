"""ManageLivingExpenseItemsUseCase のテスト"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.port.living_expense_item_repository import LivingExpenseItemRepository
from app.application.port.living_expense_repository import LivingExpenseRepository
from app.application.port.logger import Logger
from app.application.port.receipt_image_storage import ReceiptImageStoragePort
from app.application.usecase.manage_living_expense_items import (
    AddLivingExpenseItemCommand,
    DeleteLivingExpenseItemCommand,
    DeleteReceiptCommand,
    ManageLivingExpenseItemsUseCase,
    UpdateLivingExpenseItemCommand,
)
from app.domain.model.living_expense import (
    LIVING_EXPENSE_CATEGORY_ELECTRICITY,
    LIVING_EXPENSE_CATEGORY_FOOD,
    LivingExpense,
)
from app.domain.model.living_expense_item import (
    LIVING_EXPENSE_ITEM_SUBCATEGORY_DAILY_GOODS,
    LIVING_EXPENSE_ITEM_SUBCATEGORY_GROCERY,
    LivingExpenseItem,
)
from app.domain.model.money import Money
from app.domain.model.year_month import YearMonth


@pytest.fixture
def fake_living_expense_repo() -> LivingExpenseRepository:
    """Fake LivingExpenseRepository"""
    repo = MagicMock(spec=LivingExpenseRepository)
    repo.find_all = AsyncMock(return_value=[])
    repo.find_by_year_month = AsyncMock(return_value=[])
    repo.save = AsyncMock()
    repo.delete = AsyncMock()
    return repo


@pytest.fixture
def fake_item_repo() -> LivingExpenseItemRepository:
    """Fake LivingExpenseItemRepository"""
    repo = MagicMock(spec=LivingExpenseItemRepository)
    repo.find_by_living_expense_id = AsyncMock(return_value=[])
    repo.find_by_year_month = AsyncMock(return_value=[])
    repo.find_all = AsyncMock(return_value=[])
    repo.save = AsyncMock()
    repo.delete = AsyncMock()
    repo.delete_by_living_expense_id = AsyncMock()
    return repo


@pytest.fixture
def fake_image_storage() -> ReceiptImageStoragePort:
    """Fake ReceiptImageStoragePort"""
    storage = MagicMock(spec=ReceiptImageStoragePort)
    storage.validate_and_save = AsyncMock(return_value="receipts/2024-03/1.png")
    storage.delete = AsyncMock()
    return storage


@pytest.fixture
def fake_logger() -> Logger:
    """Fake Logger"""
    logger = MagicMock(spec=Logger)
    logger.info = MagicMock()
    return logger


@pytest.fixture
def usecase(
    fake_living_expense_repo: LivingExpenseRepository,
    fake_item_repo: LivingExpenseItemRepository,
    fake_image_storage: ReceiptImageStoragePort,
    fake_logger: Logger,
) -> ManageLivingExpenseItemsUseCase:
    """テスト対象のユースケース"""
    return ManageLivingExpenseItemsUseCase(
        fake_living_expense_repo, fake_item_repo, fake_image_storage, fake_logger
    )


def _receipt(
    id: int = 1,
    category: str = LIVING_EXPENSE_CATEGORY_FOOD,
    location: str = "",
    amount: int = 0,
    receipt_image_path: str | None = None,
) -> LivingExpense:
    """テスト用LivingExpenseを組み立てるヘルパー"""
    return LivingExpense(
        id=id,
        year_month=YearMonth(2024, 3),
        category=category,
        location=location,
        amount=Money(amount),
        note="",
        receipt_image_path=receipt_image_path,
    )


# --- レシート作成（画像なし） ---


async def test_create_receipt_without_image_creates_food_with_empty_location_and_zero_amount(
    usecase: ManageLivingExpenseItemsUseCase,
    fake_living_expense_repo: LivingExpenseRepository,
) -> None:
    """画像なしのレシート作成: category=food, location="", amount=0で作成される"""
    receipt = await usecase.create_receipt(2024, 3)

    assert receipt.category == LIVING_EXPENSE_CATEGORY_FOOD
    assert receipt.location == ""
    assert receipt.amount.amount == 0

    fake_living_expense_repo.save.assert_called_once()
    saved = fake_living_expense_repo.save.call_args.args[0]
    assert saved.category == LIVING_EXPENSE_CATEGORY_FOOD
    assert saved.location == ""
    assert saved.amount.amount == 0
    assert saved.receipt_image_path is None


# --- レシート作成（画像あり） ---


async def test_create_receipt_with_image_calls_validate_and_save_and_sets_path(
    usecase: ManageLivingExpenseItemsUseCase,
    fake_living_expense_repo: LivingExpenseRepository,
    fake_image_storage: ReceiptImageStoragePort,
) -> None:
    """画像ありのレシート作成: validate_and_saveが呼ばれ、成功時にreceipt_image_pathが設定される"""
    receipt = await usecase.create_receipt_with_image(2024, 3, b"dummy-image-bytes")

    fake_image_storage.validate_and_save.assert_called_once()
    assert receipt.receipt_image_path == "receipts/2024-03/1.png"

    fake_living_expense_repo.save.assert_called_once()
    saved = fake_living_expense_repo.save.call_args.args[0]
    assert saved.receipt_image_path == "receipts/2024-03/1.png"


async def test_create_receipt_with_image_validation_failure_does_not_create_receipt(
    usecase: ManageLivingExpenseItemsUseCase,
    fake_living_expense_repo: LivingExpenseRepository,
    fake_image_storage: ReceiptImageStoragePort,
) -> None:
    """画像検証失敗時: レシートを作成せずエラーが伝播する"""
    fake_image_storage.validate_and_save = AsyncMock(
        side_effect=ValueError("画像を読み込めませんでした")
    )

    with pytest.raises(ValueError, match="画像を読み込めませんでした"):
        await usecase.create_receipt_with_image(2024, 3, b"not-an-image")

    fake_living_expense_repo.save.assert_not_called()


# --- 品目追加・編集・削除による親amount再計算（4.4.4節、最重要） ---


async def test_add_item_recalculates_parent_amount(
    usecase: ManageLivingExpenseItemsUseCase,
    fake_living_expense_repo: LivingExpenseRepository,
    fake_item_repo: LivingExpenseItemRepository,
) -> None:
    """品目追加後、親LivingExpense.amountが品目合計に再計算されて保存される"""
    receipt = _receipt(id=5, amount=0)
    fake_living_expense_repo.find_all = AsyncMock(return_value=[receipt])

    added_item = LivingExpenseItem(
        id=1,
        living_expense_id=5,
        name="牛乳",
        amount=Money(200),
        sub_category=LIVING_EXPENSE_ITEM_SUBCATEGORY_GROCERY,
    )
    fake_item_repo.find_all = AsyncMock(return_value=[])  # 採番用（テーブル全体、空）
    fake_item_repo.find_by_living_expense_id = AsyncMock(return_value=[added_item])  # 再計算用

    command = AddLivingExpenseItemCommand(
        living_expense_id=5, name="牛乳", amount=200, sub_category=LIVING_EXPENSE_ITEM_SUBCATEGORY_GROCERY
    )
    await usecase.add_item(command)

    fake_item_repo.save.assert_called_once()
    fake_living_expense_repo.save.assert_called_once()
    updated_receipt = fake_living_expense_repo.save.call_args.args[0]
    assert updated_receipt.id == 5
    assert updated_receipt.amount.amount == 200


async def test_add_item_id_is_unique_across_receipts_regression(
    usecase: ManageLivingExpenseItemsUseCase,
    fake_living_expense_repo: LivingExpenseRepository,
    fake_item_repo: LivingExpenseItemRepository,
) -> None:
    """品目採番はレシートをまたいでテーブル全体で一意である（障害対応ADR-001の再発防止）

    レシートAに既にid=1の品目がある状態でレシートB(品目0件)に追加しても、
    レシートAと同じid=1にはならない（レシート単位スコープの採番に戻ると衝突し、
    UPSERTでレシートAの品目が上書きされてしまう）。
    """
    receipt_a_item = LivingExpenseItem(
        id=1,
        living_expense_id=5,
        name="牛乳",
        amount=Money(200),
        sub_category=LIVING_EXPENSE_ITEM_SUBCATEGORY_GROCERY,
    )
    receipt_b = _receipt(id=7, amount=0)
    fake_living_expense_repo.find_all = AsyncMock(return_value=[receipt_b])
    # 採番は全品目（テーブル全体）を見る。レシートB自身の品目は空でも、
    # レシートAの品目id=1が存在するため次IDは2にならなければならない
    fake_item_repo.find_all = AsyncMock(return_value=[receipt_a_item])
    fake_item_repo.find_by_living_expense_id = AsyncMock(
        return_value=[
            LivingExpenseItem(
                id=2,
                living_expense_id=7,
                name="石鹸",
                amount=Money(300),
                sub_category=LIVING_EXPENSE_ITEM_SUBCATEGORY_DAILY_GOODS,
            )
        ]
    )

    command = AddLivingExpenseItemCommand(
        living_expense_id=7,
        name="石鹸",
        amount=300,
        sub_category=LIVING_EXPENSE_ITEM_SUBCATEGORY_DAILY_GOODS,
    )
    added = await usecase.add_item(command)

    assert added.id == 2
    saved_item = fake_item_repo.save.call_args.args[0]
    assert saved_item.id == 2


async def test_update_item_recalculates_parent_amount(
    usecase: ManageLivingExpenseItemsUseCase,
    fake_living_expense_repo: LivingExpenseRepository,
    fake_item_repo: LivingExpenseItemRepository,
) -> None:
    """品目編集後、親LivingExpense.amountが再計算されて保存される"""
    receipt = _receipt(id=5, amount=200)
    fake_living_expense_repo.find_all = AsyncMock(return_value=[receipt])

    other_item = LivingExpenseItem(
        id=2,
        living_expense_id=5,
        name="石鹸",
        amount=Money(300),
        sub_category=LIVING_EXPENSE_ITEM_SUBCATEGORY_DAILY_GOODS,
    )
    edited_item = LivingExpenseItem(
        id=1,
        living_expense_id=5,
        name="牛乳（編集後）",
        amount=Money(500),
        sub_category=LIVING_EXPENSE_ITEM_SUBCATEGORY_GROCERY,
    )
    fake_item_repo.find_by_living_expense_id = AsyncMock(return_value=[edited_item, other_item])

    command = UpdateLivingExpenseItemCommand(
        item_id=1,
        living_expense_id=5,
        name="牛乳（編集後）",
        amount=500,
        sub_category=LIVING_EXPENSE_ITEM_SUBCATEGORY_GROCERY,
    )
    await usecase.update_item(command)

    fake_item_repo.save.assert_called_once()
    fake_living_expense_repo.save.assert_called_once()
    updated_receipt = fake_living_expense_repo.save.call_args.args[0]
    assert updated_receipt.amount.amount == 800


async def test_delete_item_recalculates_parent_amount_to_remaining_sum(
    usecase: ManageLivingExpenseItemsUseCase,
    fake_living_expense_repo: LivingExpenseRepository,
    fake_item_repo: LivingExpenseItemRepository,
) -> None:
    """品目削除後、親amountが残り品目の合計に再計算される"""
    receipt = _receipt(id=5, amount=500)
    fake_living_expense_repo.find_all = AsyncMock(return_value=[receipt])

    remaining_item = LivingExpenseItem(
        id=2,
        living_expense_id=5,
        name="石鹸",
        amount=Money(300),
        sub_category=LIVING_EXPENSE_ITEM_SUBCATEGORY_DAILY_GOODS,
    )
    fake_item_repo.find_by_living_expense_id = AsyncMock(return_value=[remaining_item])

    command = DeleteLivingExpenseItemCommand(item_id=1, living_expense_id=5)
    await usecase.delete_item(command)

    fake_item_repo.delete.assert_called_once_with(1)
    fake_living_expense_repo.save.assert_called_once()
    updated_receipt = fake_living_expense_repo.save.call_args.args[0]
    assert updated_receipt.amount.amount == 300


async def test_delete_item_recalculates_to_zero_when_no_items_remain(
    usecase: ManageLivingExpenseItemsUseCase,
    fake_living_expense_repo: LivingExpenseRepository,
    fake_item_repo: LivingExpenseItemRepository,
) -> None:
    """全品目削除後、親amountは0円になる"""
    receipt = _receipt(id=5, amount=300)
    fake_living_expense_repo.find_all = AsyncMock(return_value=[receipt])
    fake_item_repo.find_by_living_expense_id = AsyncMock(return_value=[])

    command = DeleteLivingExpenseItemCommand(item_id=2, living_expense_id=5)
    await usecase.delete_item(command)

    fake_living_expense_repo.save.assert_called_once()
    updated_receipt = fake_living_expense_repo.save.call_args.args[0]
    assert updated_receipt.amount.amount == 0


# --- get_receipts()の絞り込み（ゲート5で修正した重要な条件） ---


async def test_get_receipts_filters_food_category_with_empty_location_only(
    usecase: ManageLivingExpenseItemsUseCase,
    fake_living_expense_repo: LivingExpenseRepository,
    fake_item_repo: LivingExpenseItemRepository,
) -> None:
    """get_receipts(): category="food" かつ location="" のLivingExpenseのみを対象とする

    通常の簡易入力食費（locationあり）は含まれない。
    ゲート5でCritical不具合として見つかり修正された箇所の再発防止テスト。
    """
    receipt_expense = _receipt(id=1, category=LIVING_EXPENSE_CATEGORY_FOOD, location="", amount=500)
    simple_food_expense = _receipt(
        id=2, category=LIVING_EXPENSE_CATEGORY_FOOD, location="スーパー", amount=1200
    )
    non_food_expense = _receipt(
        id=3, category=LIVING_EXPENSE_CATEGORY_ELECTRICITY, location="", amount=8000
    )
    fake_living_expense_repo.find_by_year_month = AsyncMock(
        return_value=[receipt_expense, simple_food_expense, non_food_expense]
    )
    fake_item_repo.find_by_living_expense_id = AsyncMock(return_value=[])

    summaries = await usecase.get_receipts(2024, 3)

    assert len(summaries) == 1
    assert summaries[0].living_expense.id == 1


async def test_get_receipts_includes_receipts_with_zero_items(
    usecase: ManageLivingExpenseItemsUseCase,
    fake_living_expense_repo: LivingExpenseRepository,
    fake_item_repo: LivingExpenseItemRepository,
) -> None:
    """get_receipts(): 作成直後の品目0件のレシートも一覧に含まれる"""
    receipt_expense = _receipt(id=1, category=LIVING_EXPENSE_CATEGORY_FOOD, location="", amount=0)
    fake_living_expense_repo.find_by_year_month = AsyncMock(return_value=[receipt_expense])
    fake_item_repo.find_by_living_expense_id = AsyncMock(return_value=[])

    summaries = await usecase.get_receipts(2024, 3)

    assert len(summaries) == 1
    assert summaries[0].item_count == 0


# --- 小分類別集計 ---


async def test_get_sub_category_totals_includes_zero_for_unregistered_sub_category(
    usecase: ManageLivingExpenseItemsUseCase,
    fake_item_repo: LivingExpenseItemRepository,
) -> None:
    """小分類別集計: 登録0件の小分類も0円として結果に含まれる（除外されない、US-04）"""
    grocery_item = LivingExpenseItem(
        id=1,
        living_expense_id=1,
        name="牛乳",
        amount=Money(200),
        sub_category=LIVING_EXPENSE_ITEM_SUBCATEGORY_GROCERY,
    )
    fake_item_repo.find_by_year_month = AsyncMock(return_value=[grocery_item])

    totals = await usecase.get_sub_category_totals(2024, 3)

    assert totals[LIVING_EXPENSE_ITEM_SUBCATEGORY_GROCERY].amount == 200
    assert LIVING_EXPENSE_ITEM_SUBCATEGORY_DAILY_GOODS in totals
    assert totals[LIVING_EXPENSE_ITEM_SUBCATEGORY_DAILY_GOODS].amount == 0


# --- 貼り付けプレビュー・一括保存 ---


async def test_preview_paste_does_not_save(
    usecase: ManageLivingExpenseItemsUseCase,
    fake_item_repo: LivingExpenseItemRepository,
    fake_living_expense_repo: LivingExpenseRepository,
) -> None:
    """貼り付けプレビュー: 保存を行わず解析結果を返す"""
    results = usecase.preview_paste("牛乳\t200\t食品\n不正行\t二百円\t食品")

    assert len(results) == 2
    assert results[0].error is None
    assert results[1].error is not None
    fake_item_repo.save.assert_not_called()
    fake_living_expense_repo.save.assert_not_called()


async def test_save_paste_saves_all_when_all_lines_valid(
    usecase: ManageLivingExpenseItemsUseCase,
    fake_item_repo: LivingExpenseItemRepository,
    fake_living_expense_repo: LivingExpenseRepository,
) -> None:
    """貼り付け一括保存: 全行正常なら一括保存される"""
    receipt = _receipt(id=5, amount=0)
    fake_living_expense_repo.find_all = AsyncMock(return_value=[receipt])
    saved_items: list[LivingExpenseItem] = [
        LivingExpenseItem(
            id=1,
            living_expense_id=5,
            name="牛乳",
            amount=Money(200),
            sub_category=LIVING_EXPENSE_ITEM_SUBCATEGORY_GROCERY,
        ),
        LivingExpenseItem(
            id=2,
            living_expense_id=5,
            name="石鹸",
            amount=Money(300),
            sub_category=LIVING_EXPENSE_ITEM_SUBCATEGORY_DAILY_GOODS,
        ),
    ]
    fake_item_repo.find_all = AsyncMock(return_value=[])  # 採番用（テーブル全体、空）
    fake_item_repo.find_by_living_expense_id = AsyncMock(return_value=saved_items)  # 再計算用

    text = "牛乳\t200\t食品\n石鹸\t300\t生活用品"
    results = await usecase.save_paste(5, text)

    assert all(r.error is None for r in results)
    assert fake_item_repo.save.call_count == 2
    fake_living_expense_repo.save.assert_called_once()
    updated_receipt = fake_living_expense_repo.save.call_args.args[0]
    assert updated_receipt.amount.amount == 500


async def test_save_paste_saves_nothing_when_any_line_invalid(
    usecase: ManageLivingExpenseItemsUseCase,
    fake_item_repo: LivingExpenseItemRepository,
    fake_living_expense_repo: LivingExpenseRepository,
) -> None:
    """貼り付け一括保存: 1行でも不正なら1件も保存されない（All-or-Nothing、US-03 AC5）"""
    text = "牛乳\t200\t食品\n不正行\t二百円\t食品"

    results = await usecase.save_paste(5, text)

    assert any(r.error is not None for r in results)
    fake_item_repo.save.assert_not_called()
    fake_living_expense_repo.save.assert_not_called()


# --- レシート削除 ---


async def test_delete_receipt_cascades_items_and_deletes_image_file(
    usecase: ManageLivingExpenseItemsUseCase,
    fake_living_expense_repo: LivingExpenseRepository,
    fake_item_repo: LivingExpenseItemRepository,
    fake_image_storage: ReceiptImageStoragePort,
) -> None:
    """レシート削除: 品目もカスケード削除され、画像ファイルがある場合はstorage.deleteが呼ばれる"""
    receipt = _receipt(id=5, receipt_image_path="receipts/2024-03/5.png")
    fake_living_expense_repo.find_all = AsyncMock(return_value=[receipt])

    await usecase.delete_receipt(DeleteReceiptCommand(living_expense_id=5))

    fake_item_repo.delete_by_living_expense_id.assert_called_once_with(5)
    fake_image_storage.delete.assert_called_once_with("receipts/2024-03/5.png")
    fake_living_expense_repo.delete.assert_called_once_with(5)


async def test_delete_receipt_without_image_does_not_call_storage_delete(
    usecase: ManageLivingExpenseItemsUseCase,
    fake_living_expense_repo: LivingExpenseRepository,
    fake_item_repo: LivingExpenseItemRepository,
    fake_image_storage: ReceiptImageStoragePort,
) -> None:
    """レシート削除: 画像がない場合はstorage.deleteが呼ばれない"""
    receipt = _receipt(id=5, receipt_image_path=None)
    fake_living_expense_repo.find_all = AsyncMock(return_value=[receipt])

    await usecase.delete_receipt(DeleteReceiptCommand(living_expense_id=5))

    fake_item_repo.delete_by_living_expense_id.assert_called_once_with(5)
    fake_image_storage.delete.assert_not_called()
    fake_living_expense_repo.delete.assert_called_once_with(5)
