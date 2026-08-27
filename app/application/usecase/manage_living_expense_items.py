"""レシート・生活費品目の管理ユースケース"""
from __future__ import annotations

from dataclasses import dataclass

from app.application.port.living_expense_item_repository import LivingExpenseItemRepository
from app.application.port.living_expense_repository import LivingExpenseRepository
from app.application.port.logger import Logger
from app.application.port.receipt_image_storage import ReceiptImageStoragePort
from app.domain.model.living_expense import LIVING_EXPENSE_CATEGORY_FOOD, LivingExpense
from app.domain.model.living_expense_item import (
    LIVING_EXPENSE_ITEM_SUBCATEGORIES,
    LivingExpenseItem,
)
from app.domain.model.log_context import LogContext
from app.domain.model.money import Money
from app.domain.model.year_month import YearMonth
from app.domain.service.receipt_paste_parser import ParsedReceiptLine, parse_receipt_paste_text


@dataclass(frozen=True)
class AddLivingExpenseItemCommand:
    """品目追加コマンド"""

    living_expense_id: int
    """親レシートのID"""
    name: str
    """品目名"""
    amount: int
    """金額"""
    sub_category: str
    """小分類"""


@dataclass(frozen=True)
class UpdateLivingExpenseItemCommand:
    """品目編集コマンド"""

    item_id: int
    """品目ID"""
    living_expense_id: int
    """親レシートのID（親金額の再計算に使用）"""
    name: str
    """品目名"""
    amount: int
    """金額"""
    sub_category: str
    """小分類"""


@dataclass(frozen=True)
class DeleteLivingExpenseItemCommand:
    """品目削除コマンド"""

    item_id: int
    """品目ID"""
    living_expense_id: int
    """親レシートのID（親金額の再計算に使用）"""


@dataclass(frozen=True)
class DeleteReceiptCommand:
    """レシート削除コマンド"""

    living_expense_id: int
    """レシート（親LivingExpense）のID"""


@dataclass(frozen=True)
class ReceiptSummary:
    """レシート一覧表示用データ（SCR-01）"""

    living_expense: LivingExpense
    """親レシート"""
    item_count: int
    """品目件数"""


class ManageLivingExpenseItemsUseCase:
    """レシート・生活費品目の管理ユースケース"""

    def __init__(
        self,
        living_expense_repo: LivingExpenseRepository,
        living_expense_item_repo: LivingExpenseItemRepository,
        receipt_image_storage: ReceiptImageStoragePort,
        logger: Logger,
    ) -> None:
        self._living_expense_repo = living_expense_repo
        self._living_expense_item_repo = living_expense_item_repo
        self._receipt_image_storage = receipt_image_storage
        self._logger = logger

    async def create_receipt(self, year: int, month: int) -> LivingExpense:
        """レシート（画像なし）を新規作成する（品目0件、金額0円）"""
        ym = YearMonth(year, month)
        receipt = await self._save_new_receipt(ym, receipt_image_path=None)

        context = LogContext(
            screen="month",
            context={"year": year, "month": month, "action": "create_receipt"},
        )
        self._logger.info(f"レシート作成（画像なし）: {year}年{month}月", context)
        return receipt

    async def create_receipt_with_image(
        self, year: int, month: int, image_data: bytes
    ) -> LivingExpense:
        """レシート（画像付き）を新規作成する（品目0件、金額0円）

        Raises:
            ValueError: 画像として読み込めない場合（保存は行わない）
        """
        next_id = await self._next_living_expense_id()
        # 画像検証・保存を先に行い、失敗時はレシートを作成しない
        relative_path = await self._receipt_image_storage.validate_and_save(
            year, month, next_id, image_data
        )

        ym = YearMonth(year, month)
        receipt = LivingExpense(
            id=next_id,
            year_month=ym,
            category=LIVING_EXPENSE_CATEGORY_FOOD,
            location="",
            amount=Money(0),
            note="",
            receipt_image_path=relative_path,
        )
        await self._living_expense_repo.save(receipt)

        context = LogContext(
            screen="month",
            context={"year": year, "month": month, "action": "create_receipt_with_image"},
        )
        self._logger.info(f"レシート作成（画像付き）: {year}年{month}月", context)
        return receipt

    async def delete_receipt(self, command: DeleteReceiptCommand) -> None:
        """レシート（親＋品目全件＋画像ファイル）を削除する"""
        receipt = await self._find_receipt(command.living_expense_id)

        await self._living_expense_item_repo.delete_by_living_expense_id(
            command.living_expense_id
        )
        if receipt is not None and receipt.receipt_image_path:
            await self._receipt_image_storage.delete(receipt.receipt_image_path)
        await self._living_expense_repo.delete(command.living_expense_id)

        context = LogContext(
            screen="month",
            context={
                "living_expense_id": command.living_expense_id,
                "action": "delete_receipt",
            },
        )
        self._logger.info(f"レシート削除: ID {command.living_expense_id}", context)

    async def add_item(self, command: AddLivingExpenseItemCommand) -> LivingExpenseItem:
        """品目を1件追加する（保存の都度、親レシートの金額を再計算する）"""
        next_id = await self._next_living_expense_item_id()

        item = LivingExpenseItem(
            id=next_id,
            living_expense_id=command.living_expense_id,
            name=command.name,
            amount=Money(command.amount),
            sub_category=command.sub_category,
        )
        await self._living_expense_item_repo.save(item)
        await self._recalculate_receipt_amount(command.living_expense_id)

        context = LogContext(
            screen="month",
            context={"living_expense_id": command.living_expense_id, "action": "add_item"},
        )
        self._logger.info(f"品目追加: {command.name} ({command.amount}円)", context)
        return item

    async def update_item(self, command: UpdateLivingExpenseItemCommand) -> None:
        """品目を編集する（保存の都度、親レシートの金額を再計算する）"""
        item = LivingExpenseItem(
            id=command.item_id,
            living_expense_id=command.living_expense_id,
            name=command.name,
            amount=Money(command.amount),
            sub_category=command.sub_category,
        )
        await self._living_expense_item_repo.save(item)
        await self._recalculate_receipt_amount(command.living_expense_id)

        context = LogContext(
            screen="month",
            context={"item_id": command.item_id, "action": "update_item"},
        )
        self._logger.info(f"品目編集: ID {command.item_id}", context)

    async def delete_item(self, command: DeleteLivingExpenseItemCommand) -> None:
        """品目を削除する（削除の都度、親レシートの金額を再計算する）"""
        await self._living_expense_item_repo.delete(command.item_id)
        await self._recalculate_receipt_amount(command.living_expense_id)

        context = LogContext(
            screen="month",
            context={"item_id": command.item_id, "action": "delete_item"},
        )
        self._logger.info(f"品目削除: ID {command.item_id}", context)

    def preview_paste(self, text: str) -> list[ParsedReceiptLine]:
        """貼り付けテキストを解析してプレビュー行を返す（保存は行わない）"""
        return parse_receipt_paste_text(text)

    async def save_paste(self, living_expense_id: int, text: str) -> list[ParsedReceiptLine]:
        """貼り付けテキストをサーバ側で再検証し、全行正常な場合のみ一括保存する

        1行でも不正な場合は1件も保存しない（US-03 AC5）。

        Returns:
            解析結果の行リスト。errorが1件でもあれば保存されていない
        """
        lines = parse_receipt_paste_text(text)
        if any(line.error is not None for line in lines):
            return lines

        next_id = await self._next_living_expense_item_id()

        for line in lines:
            assert line.name is not None
            assert line.amount is not None
            assert line.sub_category is not None
            item = LivingExpenseItem(
                id=next_id,
                living_expense_id=living_expense_id,
                name=line.name,
                amount=Money(line.amount),
                sub_category=line.sub_category,
            )
            await self._living_expense_item_repo.save(item)
            next_id += 1

        await self._recalculate_receipt_amount(living_expense_id)

        context = LogContext(
            screen="month",
            context={
                "living_expense_id": living_expense_id,
                "action": "save_paste",
                "count": len(lines),
            },
        )
        self._logger.info(f"貼り付け一括登録: {len(lines)}件", context)
        return lines

    async def get_receipt(self, living_expense_id: int) -> LivingExpense | None:
        """レシート（親LivingExpense）を1件取得する"""
        return await self._find_receipt(living_expense_id)

    async def get_items(self, living_expense_id: int) -> list[LivingExpenseItem]:
        """指定レシートに紐づく品目一覧を取得する"""
        return await self._living_expense_item_repo.find_by_living_expense_id(living_expense_id)

    async def get_receipts(self, year: int, month: int) -> list[ReceiptSummary]:
        """対象年月のレシート一覧を取得する（品目0件の新規作成直後のレシートも含む）

        レシート経由で作成された `LivingExpense`（`category="food"`, `location=""`）を対象とする。
        簡易入力の食費は食費カテゴリでも `location` の入力が必須（3.3節）のため、
        `location==""` で両者を区別できる。品目0件のレシートも一覧に含めることで、
        新規作成直後にSCR-03（品目一覧編集）へ到達できるようにする（基本設計3.2節）。
        """
        ym = YearMonth(year, month)
        expenses = await self._living_expense_repo.find_by_year_month(ym)
        receipt_expenses = [
            e
            for e in expenses
            if e.category == LIVING_EXPENSE_CATEGORY_FOOD and e.location == ""
        ]

        summaries: list[ReceiptSummary] = []
        for expense in receipt_expenses:
            items = await self._living_expense_item_repo.find_by_living_expense_id(expense.id)
            summaries.append(ReceiptSummary(living_expense=expense, item_count=len(items)))
        return summaries

    async def get_sub_category_totals(self, year: int, month: int) -> dict[str, Money]:
        """指定年月の小分類別集計を取得する（登録が0件の小分類も0円で含める、US-04）"""
        ym = YearMonth(year, month)
        items = await self._living_expense_item_repo.find_by_year_month(ym)

        totals: dict[str, int] = {sub: 0 for sub in LIVING_EXPENSE_ITEM_SUBCATEGORIES}
        for item in items:
            if item.sub_category in totals:
                totals[item.sub_category] += item.amount.amount

        return {sub: Money(total) for sub, total in totals.items()}

    async def _save_new_receipt(
        self, ym: YearMonth, receipt_image_path: str | None
    ) -> LivingExpense:
        """品目0件・金額0円のレシートを新規作成して保存する（4.4.4節）"""
        next_id = await self._next_living_expense_id()
        receipt = LivingExpense(
            id=next_id,
            year_month=ym,
            category=LIVING_EXPENSE_CATEGORY_FOOD,
            location="",
            amount=Money(0),
            note="",
            receipt_image_path=receipt_image_path,
        )
        await self._living_expense_repo.save(receipt)
        return receipt

    async def _next_living_expense_id(self) -> int:
        """LivingExpenseの次の採番IDを決定する"""
        all_expenses = await self._living_expense_repo.find_all()
        return max([e.id for e in all_expenses], default=0) + 1

    async def _next_living_expense_item_id(self) -> int:
        """LivingExpenseItemの次の採番ID（レシートをまたいでテーブル全体で一意）を決定する

        レシート単位でスコープした採番は、別レシートの品目とIDが衝突し、
        主キーによるUPSERTで互いの品目を上書きし合う不具合を起こす（障害対応ADR-001）。
        """
        all_items = await self._living_expense_item_repo.find_all()
        return max([i.id for i in all_items], default=0) + 1

    async def _find_receipt(self, living_expense_id: int) -> LivingExpense | None:
        """IDでレシート（親LivingExpense）を検索する"""
        all_expenses = await self._living_expense_repo.find_all()
        return next((e for e in all_expenses if e.id == living_expense_id), None)

    async def _recalculate_receipt_amount(self, living_expense_id: int) -> None:
        """品目保存の都度、親レシートのamountを品目合計で再計算する（4.4.4節）"""
        receipt = await self._find_receipt(living_expense_id)
        if receipt is None:
            return

        items = await self._living_expense_item_repo.find_by_living_expense_id(
            living_expense_id
        )
        total = sum(i.amount.amount for i in items)

        updated = LivingExpense(
            id=receipt.id,
            year_month=receipt.year_month,
            category=receipt.category,
            location=receipt.location,
            amount=Money(total),
            note=receipt.note,
            receipt_image_path=receipt.receipt_image_path,
        )
        await self._living_expense_repo.save(updated)
