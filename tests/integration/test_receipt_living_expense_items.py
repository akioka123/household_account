"""レシート金額抽出・生活費入力の詳細化: 結合テスト（DBなし）

基本設計4.3節のエンドポイント10本を対象に、`TestClient` + `app.dependency_overrides` で
`ManageLivingExpensesUseCase` / `ManageLivingExpenseItemsUseCase` をスタブに差し替えて検証する。
プロダクトコードの修正は行わない（不具合は統括に報告する）。
"""
from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.application.usecase.manage_living_expense_items import (
    AddLivingExpenseItemCommand,
    DeleteLivingExpenseItemCommand,
    DeleteReceiptCommand,
    ReceiptSummary,
    UpdateLivingExpenseItemCommand,
)
from app.application.usecase.manage_living_expenses import (
    AddLivingExpenseCommand,
    DeleteLivingExpenseCommand,
    LivingExpenseData,
    UpdateLivingExpenseCommand,
)
from app.domain.model.living_expense import (
    LIVING_EXPENSE_CATEGORIES,
    LIVING_EXPENSE_CATEGORY_FOOD,
    LivingExpense,
)
from app.domain.model.living_expense_item import (
    LIVING_EXPENSE_ITEM_SUBCATEGORIES,
    LivingExpenseItem,
)
from app.domain.model.money import Money
from app.domain.model.year_month import YearMonth
from app.domain.service.receipt_paste_parser import parse_receipt_paste_text
from app.main import app
from app.presentation.web.routers.month_router import (
    provide_manage_living_expense_items_uc,
    provide_manage_living_expenses_uc,
)


class StubManageLivingExpensesUseCase:
    """DBを使わないManageLivingExpensesUseCaseのスタブ（既存の簡易入力）"""

    def __init__(self) -> None:
        self.expenses: list[LivingExpense] = []
        self.add_calls: list[AddLivingExpenseCommand] = []
        self.update_calls: list[UpdateLivingExpenseCommand] = []
        self.delete_calls: list[DeleteLivingExpenseCommand] = []
        self.raise_on_add: ValueError | None = None
        self.raise_on_update: ValueError | None = None

    async def add_living_expense(self, command: AddLivingExpenseCommand) -> None:
        self.add_calls.append(command)
        if self.raise_on_add is not None:
            raise self.raise_on_add
        ym = YearMonth(command.year, command.month)
        next_id = max([e.id for e in self.expenses], default=0) + 1
        self.expenses.append(
            LivingExpense(
                id=next_id,
                year_month=ym,
                category=command.category,
                location=(command.location or "").strip(),
                amount=Money(command.amount),
                note=command.note or "",
            )
        )

    async def update_living_expense(self, command: UpdateLivingExpenseCommand) -> None:
        self.update_calls.append(command)
        if self.raise_on_update is not None:
            raise self.raise_on_update
        ym = YearMonth(command.year, command.month)
        self.expenses = [e for e in self.expenses if e.id != command.living_expense_id]
        self.expenses.append(
            LivingExpense(
                id=command.living_expense_id,
                year_month=ym,
                category=command.category,
                location=(command.location or "").strip(),
                amount=Money(command.amount),
                note=command.note or "",
            )
        )

    async def delete_living_expense(self, command: DeleteLivingExpenseCommand) -> None:
        self.delete_calls.append(command)
        self.expenses = [e for e in self.expenses if e.id != command.living_expense_id]

    async def get_living_expense_data(self, year: int, month: int) -> LivingExpenseData:
        ym = YearMonth(year, month)
        by_category: dict[str, list[LivingExpense]] = {cat: [] for cat in LIVING_EXPENSE_CATEGORIES}
        for e in self.expenses:
            if e.year_month == ym and e.category in by_category:
                by_category[e.category].append(e)
        totals = {
            cat: Money(sum(i.amount.amount for i in by_category[cat])) for cat in LIVING_EXPENSE_CATEGORIES
        }
        return LivingExpenseData(by_category=by_category, totals_by_category=totals)


class StubManageLivingExpenseItemsUseCase:
    """DBを使わないManageLivingExpenseItemsUseCaseのスタブ（レシート・品目、メモリ保持）"""

    def __init__(self) -> None:
        self.receipts: dict[int, LivingExpense] = {}
        self.items: dict[int, list[LivingExpenseItem]] = {}
        self._next_receipt_id = 1
        self.raise_on_image: ValueError | None = None
        self.deleted_receipt_ids: list[int] = []
        self.add_item_calls: list[AddLivingExpenseItemCommand] = []
        self.update_item_calls: list[UpdateLivingExpenseItemCommand] = []
        self.delete_item_calls: list[DeleteLivingExpenseItemCommand] = []

    async def create_receipt(self, year: int, month: int) -> LivingExpense:
        ym = YearMonth(year, month)
        rid = self._next_receipt_id
        self._next_receipt_id += 1
        receipt = LivingExpense(
            id=rid,
            year_month=ym,
            category=LIVING_EXPENSE_CATEGORY_FOOD,
            location="",
            amount=Money(0),
            note="",
        )
        self.receipts[rid] = receipt
        self.items[rid] = []
        return receipt

    async def create_receipt_with_image(
        self, year: int, month: int, image_data: bytes
    ) -> LivingExpense:
        if self.raise_on_image is not None:
            raise self.raise_on_image
        ym = YearMonth(year, month)
        rid = self._next_receipt_id
        self._next_receipt_id += 1
        receipt = LivingExpense(
            id=rid,
            year_month=ym,
            category=LIVING_EXPENSE_CATEGORY_FOOD,
            location="",
            amount=Money(0),
            note="",
            receipt_image_path=f"receipts/{year:04d}-{month:02d}/{rid}.jpg",
        )
        self.receipts[rid] = receipt
        self.items[rid] = []
        return receipt

    async def delete_receipt(self, command: DeleteReceiptCommand) -> None:
        self.deleted_receipt_ids.append(command.living_expense_id)
        self.receipts.pop(command.living_expense_id, None)
        self.items.pop(command.living_expense_id, None)

    async def add_item(self, command: AddLivingExpenseItemCommand) -> LivingExpenseItem:
        self.add_item_calls.append(command)
        items = self.items.setdefault(command.living_expense_id, [])
        next_id = max([i.id for i in items], default=0) + 1
        item = LivingExpenseItem(
            id=next_id,
            living_expense_id=command.living_expense_id,
            name=command.name,
            amount=Money(command.amount),
            sub_category=command.sub_category,
        )
        items.append(item)
        self._recalc(command.living_expense_id)
        return item

    async def update_item(self, command: UpdateLivingExpenseItemCommand) -> None:
        self.update_item_calls.append(command)
        items = self.items.get(command.living_expense_id, [])
        for idx, existing in enumerate(items):
            if existing.id == command.item_id:
                items[idx] = LivingExpenseItem(
                    id=command.item_id,
                    living_expense_id=command.living_expense_id,
                    name=command.name,
                    amount=Money(command.amount),
                    sub_category=command.sub_category,
                )
        self._recalc(command.living_expense_id)

    async def delete_item(self, command: DeleteLivingExpenseItemCommand) -> None:
        self.delete_item_calls.append(command)
        items = self.items.get(command.living_expense_id, [])
        self.items[command.living_expense_id] = [i for i in items if i.id != command.item_id]
        self._recalc(command.living_expense_id)

    def preview_paste(self, text: str):
        return parse_receipt_paste_text(text)

    async def save_paste(self, living_expense_id: int, text: str):
        lines = parse_receipt_paste_text(text)
        if any(line.error is not None for line in lines):
            return lines
        items = self.items.setdefault(living_expense_id, [])
        next_id = max([i.id for i in items], default=0) + 1
        for line in lines:
            assert line.name is not None
            assert line.amount is not None
            assert line.sub_category is not None
            items.append(
                LivingExpenseItem(
                    id=next_id,
                    living_expense_id=living_expense_id,
                    name=line.name,
                    amount=Money(line.amount),
                    sub_category=line.sub_category,
                )
            )
            next_id += 1
        self._recalc(living_expense_id)
        return lines

    async def get_receipt(self, living_expense_id: int) -> LivingExpense | None:
        return self.receipts.get(living_expense_id)

    async def get_items(self, living_expense_id: int) -> list[LivingExpenseItem]:
        return self.items.get(living_expense_id, [])

    async def get_receipts(self, year: int, month: int) -> list[ReceiptSummary]:
        ym = YearMonth(year, month)
        result: list[ReceiptSummary] = []
        for rid, receipt in self.receipts.items():
            if receipt.year_month == ym:
                result.append(
                    ReceiptSummary(living_expense=receipt, item_count=len(self.items.get(rid, [])))
                )
        return result

    async def get_sub_category_totals(self, year: int, month: int) -> dict[str, Money]:
        ym = YearMonth(year, month)
        totals: dict[str, int] = {sub: 0 for sub in LIVING_EXPENSE_ITEM_SUBCATEGORIES}
        for rid, receipt in self.receipts.items():
            if receipt.year_month != ym:
                continue
            for item in self.items.get(rid, []):
                if item.sub_category in totals:
                    totals[item.sub_category] += item.amount.amount
        return {sub: Money(total) for sub, total in totals.items()}

    def _recalc(self, living_expense_id: int) -> None:
        receipt = self.receipts.get(living_expense_id)
        if receipt is None:
            return
        total = sum(i.amount.amount for i in self.items.get(living_expense_id, []))
        self.receipts[living_expense_id] = LivingExpense(
            id=receipt.id,
            year_month=receipt.year_month,
            category=receipt.category,
            location=receipt.location,
            amount=Money(total),
            note=receipt.note,
            receipt_image_path=receipt.receipt_image_path,
        )


def _client(
    living_expenses_uc: StubManageLivingExpensesUseCase,
    living_items_uc: StubManageLivingExpenseItemsUseCase,
) -> TestClient:
    """スタブを注入したTestClientを作成"""
    app.dependency_overrides[provide_manage_living_expenses_uc] = lambda: living_expenses_uc
    app.dependency_overrides[provide_manage_living_expense_items_uc] = lambda: living_items_uc
    return TestClient(app)


@pytest.fixture()
def stubs() -> tuple[StubManageLivingExpensesUseCase, StubManageLivingExpenseItemsUseCase]:
    return StubManageLivingExpensesUseCase(), StubManageLivingExpenseItemsUseCase()


# --- 1. GET /month/{y}/{m}/tab/living ---------------------------------------------------


def test_living_tab_includes_simple_list_receipts_and_sub_category_totals(
    stubs: tuple[StubManageLivingExpensesUseCase, StubManageLivingExpenseItemsUseCase],
) -> None:
    """IT-LIV-01: 生活費タブの応答に簡易入力一覧・レシート一覧・小分類別集計が含まれる"""
    living_expenses_uc, living_items_uc = stubs
    living_expenses_uc.expenses.append(
        LivingExpense(
            id=1,
            year_month=YearMonth(2026, 3),
            category="electricity",
            location="",
            amount=Money(8000),
            note="",
        )
    )
    living_items_uc.receipts[10] = LivingExpense(
        id=10,
        year_month=YearMonth(2026, 3),
        category=LIVING_EXPENSE_CATEGORY_FOOD,
        location="",
        amount=Money(500),
        note="",
    )
    living_items_uc.items[10] = [
        LivingExpenseItem(id=1, living_expense_id=10, name="とうふ", amount=Money(108), sub_category="grocery"),
        LivingExpenseItem(id=2, living_expense_id=10, name="ラップ", amount=Money(298), sub_category="daily_goods"),
    ]

    try:
        with _client(living_expenses_uc, living_items_uc) as client:
            response = client.get("/month/2026/3/tab/living")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    # 既存簡易入力一覧（電気代）
    assert "電気代" in response.text
    assert "8,000円" in response.text
    # レシート一覧（品目件数・合計金額）
    assert "品目 2件" in response.text
    assert "500円" in response.text
    # 小分類別集計（食品・生活用品の内部値ラベル）
    assert "食品" in response.text
    assert "生活用品" in response.text
    assert "108" in response.text
    assert "298" in response.text


def test_living_tab_zero_item_receipt_is_included_in_totals_as_zero(
    stubs: tuple[StubManageLivingExpensesUseCase, StubManageLivingExpenseItemsUseCase],
) -> None:
    """IT-LIV-02: 品目0件の小分類も0円として表示される（US-04 AC4）"""
    living_expenses_uc, living_items_uc = stubs

    try:
        with _client(living_expenses_uc, living_items_uc) as client:
            response = client.get("/month/2026/3/tab/living")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert "0円" in response.text


# --- 2. POST /month/{y}/{m}/receipts（画像なし） ------------------------------------------


def test_create_receipt_without_image_reaches_item_edit_area_with_zero_items(
    stubs: tuple[StubManageLivingExpensesUseCase, StubManageLivingExpenseItemsUseCase],
) -> None:
    """IT-LIV-03: レシート作成直後（品目0件）でも編集領域に到達できる（ゲート5 Critical不具合の再発防止）"""
    living_expenses_uc, living_items_uc = stubs

    try:
        with _client(living_expenses_uc, living_items_uc) as client:
            response = client.post("/month/2026/3/receipts")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert 1 in living_items_uc.receipts
    # SCR-03（品目一覧編集）に到達: 品目0件でも編集領域（品目追加フォーム）が表示される
    assert "品目 0件" in response.text
    assert "品目は登録されていません。" in response.text
    assert "品目追加" in response.text
    # 作成直後のレシートは details が open 状態（active_receipt_id）で表示される
    assert "open" in response.text


# --- 3. POST /month/{y}/{m}/receipts/image ------------------------------------------------


def test_create_receipt_with_image_multipart_invokes_usecase(
    stubs: tuple[StubManageLivingExpensesUseCase, StubManageLivingExpenseItemsUseCase],
) -> None:
    """IT-LIV-04: multipart送信でユースケースの画像あり作成が呼ばれる"""
    living_expenses_uc, living_items_uc = stubs

    try:
        with _client(living_expenses_uc, living_items_uc) as client:
            response = client.post(
                "/month/2026/3/receipts/image",
                files={"image": ("receipt.jpg", b"fake-image-bytes", "image/jpeg")},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert len(living_items_uc.receipts) == 1
    created = next(iter(living_items_uc.receipts.values()))
    assert created.receipt_image_path is not None
    assert "品目 0件" in response.text


def test_create_receipt_with_image_validation_failure_shows_error(
    stubs: tuple[StubManageLivingExpensesUseCase, StubManageLivingExpenseItemsUseCase],
) -> None:
    """IT-LIV-05: 画像検証失敗時（ユースケースが例外）はエラー応答になり、レシートは作成されない"""
    living_expenses_uc, living_items_uc = stubs
    living_items_uc.raise_on_image = ValueError(
        "画像を読み込めませんでした。JPEGまたはPNG形式のファイルを選択してください"
    )

    try:
        with _client(living_expenses_uc, living_items_uc) as client:
            response = client.post(
                "/month/2026/3/receipts/image",
                files={"image": ("not-an-image.txt", b"not an image", "text/plain")},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert "画像を読み込めませんでした。JPEGまたはPNG形式のファイルを選択してください" in response.text
    assert living_items_uc.receipts == {}


# --- 4. GET /month/{y}/{m}/receipts/{id}/image --------------------------------------------


def test_get_receipt_image_returns_binary_with_content_type(
    stubs: tuple[StubManageLivingExpensesUseCase, StubManageLivingExpenseItemsUseCase],
) -> None:
    """IT-LIV-06: 保存済み画像のバイナリがContent-Type付きで返る"""
    living_expenses_uc, living_items_uc = stubs

    # ルーターはPortを介さずプロジェクトルート直下の data/ を直接参照するため、
    # 結合テストでも同じ場所に一時ファイルを用意する（.gitignore対象の /data/ 配下）
    project_root = Path(__file__).resolve().parents[2]
    image_dir = project_root / "data" / "receipts" / "2026-03"
    image_dir.mkdir(parents=True, exist_ok=True)
    image_path = image_dir / "10.jpg"
    image_path.write_bytes(b"\xff\xd8\xff\xe0fake-jpeg-body")

    living_items_uc.receipts[10] = LivingExpense(
        id=10,
        year_month=YearMonth(2026, 3),
        category=LIVING_EXPENSE_CATEGORY_FOOD,
        location="",
        amount=Money(0),
        note="",
        receipt_image_path="receipts/2026-03/10.jpg",
    )

    try:
        with _client(living_expenses_uc, living_items_uc) as client:
            response = client.get("/month/2026/3/receipts/10/image")
    finally:
        app.dependency_overrides.clear()
        image_path.unlink(missing_ok=True)

    assert response.status_code == 200
    assert response.content == b"\xff\xd8\xff\xe0fake-jpeg-body"
    assert response.headers["content-type"] in ("image/jpeg", "application/octet-stream")


def test_get_receipt_image_missing_file_returns_404(
    stubs: tuple[StubManageLivingExpensesUseCase, StubManageLivingExpenseItemsUseCase],
) -> None:
    """IT-LIV-07: 画像ファイルが存在しない場合は404を返す"""
    living_expenses_uc, living_items_uc = stubs
    living_items_uc.receipts[10] = LivingExpense(
        id=10,
        year_month=YearMonth(2026, 3),
        category=LIVING_EXPENSE_CATEGORY_FOOD,
        location="",
        amount=Money(0),
        note="",
        receipt_image_path="receipts/2026-03/does-not-exist.jpg",
    )

    try:
        with _client(living_expenses_uc, living_items_uc) as client:
            response = client.get("/month/2026/3/receipts/10/image")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404


def test_get_receipt_image_unknown_receipt_returns_404(
    stubs: tuple[StubManageLivingExpensesUseCase, StubManageLivingExpenseItemsUseCase],
) -> None:
    """IT-LIV-08: 存在しないレシートIDの場合は404を返す"""
    living_expenses_uc, living_items_uc = stubs

    try:
        with _client(living_expenses_uc, living_items_uc) as client:
            response = client.get("/month/2026/3/receipts/999/image")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404


# --- 5. POST /month/{y}/{m}/receipts/{id}/delete -------------------------------------------


def test_delete_receipt_invokes_usecase_and_updates_list(
    stubs: tuple[StubManageLivingExpensesUseCase, StubManageLivingExpenseItemsUseCase],
) -> None:
    """IT-LIV-09: レシート削除が呼ばれ、一覧が更新された応答になる"""
    living_expenses_uc, living_items_uc = stubs
    living_items_uc.receipts[10] = LivingExpense(
        id=10,
        year_month=YearMonth(2026, 3),
        category=LIVING_EXPENSE_CATEGORY_FOOD,
        location="",
        amount=Money(500),
        note="",
    )
    living_items_uc.items[10] = [
        LivingExpenseItem(id=1, living_expense_id=10, name="とうふ", amount=Money(500), sub_category="grocery")
    ]

    try:
        with _client(living_expenses_uc, living_items_uc) as client:
            response = client.post("/month/2026/3/receipts/10/delete")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert living_items_uc.deleted_receipt_ids == [10]
    assert "レシートは登録されていません。" in response.text


# --- 6. POST /month/{y}/{m}/receipts/{id}/items -------------------------------------------


def test_add_receipt_item_invokes_usecase_and_updates_list_and_totals(
    stubs: tuple[StubManageLivingExpensesUseCase, StubManageLivingExpenseItemsUseCase],
) -> None:
    """IT-LIV-10: 品目追加が呼ばれ、応答に追加後の一覧・集計が反映される"""
    living_expenses_uc, living_items_uc = stubs
    living_items_uc.receipts[10] = LivingExpense(
        id=10,
        year_month=YearMonth(2026, 3),
        category=LIVING_EXPENSE_CATEGORY_FOOD,
        location="",
        amount=Money(0),
        note="",
    )
    living_items_uc.items[10] = []

    try:
        with _client(living_expenses_uc, living_items_uc) as client:
            response = client.post(
                "/month/2026/3/receipts/10/items",
                data={"name": "にんじん", "amount": "158", "sub_category": "grocery"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert len(living_items_uc.add_item_calls) == 1
    assert living_items_uc.add_item_calls[0].name == "にんじん"
    assert "にんじん" in response.text
    assert "158円" in response.text
    # 親レシートの合計が再計算されている
    assert living_items_uc.receipts[10].amount.amount == 158


def test_add_receipt_item_negative_amount_is_rejected(
    stubs: tuple[StubManageLivingExpensesUseCase, StubManageLivingExpenseItemsUseCase],
) -> None:
    """IT-LIV-11(境界値): 0未満の金額はスキーマ検証エラーとして拒否される（US-02 AC2）"""
    living_expenses_uc, living_items_uc = stubs
    living_items_uc.receipts[10] = LivingExpense(
        id=10,
        year_month=YearMonth(2026, 3),
        category=LIVING_EXPENSE_CATEGORY_FOOD,
        location="",
        amount=Money(0),
        note="",
    )
    living_items_uc.items[10] = []

    try:
        with _client(living_expenses_uc, living_items_uc) as client:
            response = client.post(
                "/month/2026/3/receipts/10/items",
                data={"name": "不正データ", "amount": "-1", "sub_category": "grocery"},
            )
    finally:
        app.dependency_overrides.clear()

    # FastAPI の Form(int) 変換自体は負数も受け付けるため、
    # ドメインの LivingExpenseItem.__post_init__ の不変条件検証（ValueError）で拒否される
    assert response.status_code == 200
    assert living_items_uc.items[10] == []


# --- 7. POST /month/{y}/{m}/receipt-items/{item_id} ----------------------------------------


def test_update_receipt_item_invokes_usecase(
    stubs: tuple[StubManageLivingExpensesUseCase, StubManageLivingExpenseItemsUseCase],
) -> None:
    """IT-LIV-12: 品目編集が呼ばれる"""
    living_expenses_uc, living_items_uc = stubs
    living_items_uc.receipts[10] = LivingExpense(
        id=10,
        year_month=YearMonth(2026, 3),
        category=LIVING_EXPENSE_CATEGORY_FOOD,
        location="",
        amount=Money(108),
        note="",
    )
    living_items_uc.items[10] = [
        LivingExpenseItem(id=1, living_expense_id=10, name="とうふ", amount=Money(108), sub_category="grocery")
    ]

    try:
        with _client(living_expenses_uc, living_items_uc) as client:
            response = client.post(
                "/month/2026/3/receipt-items/1",
                data={
                    "living_expense_id": "10",
                    "name": "絹ごしとうふ",
                    "amount": "120",
                    "sub_category": "grocery",
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert len(living_items_uc.update_item_calls) == 1
    assert living_items_uc.update_item_calls[0].name == "絹ごしとうふ"
    assert "絹ごしとうふ" in response.text
    assert living_items_uc.receipts[10].amount.amount == 120


# --- 8. POST /month/{y}/{m}/receipt-items/{item_id}/delete ---------------------------------


def test_delete_receipt_item_invokes_usecase(
    stubs: tuple[StubManageLivingExpensesUseCase, StubManageLivingExpenseItemsUseCase],
) -> None:
    """IT-LIV-13: 品目削除が呼ばれる"""
    living_expenses_uc, living_items_uc = stubs
    living_items_uc.receipts[10] = LivingExpense(
        id=10,
        year_month=YearMonth(2026, 3),
        category=LIVING_EXPENSE_CATEGORY_FOOD,
        location="",
        amount=Money(108),
        note="",
    )
    living_items_uc.items[10] = [
        LivingExpenseItem(id=1, living_expense_id=10, name="とうふ", amount=Money(108), sub_category="grocery")
    ]

    try:
        with _client(living_expenses_uc, living_items_uc) as client:
            response = client.post(
                "/month/2026/3/receipt-items/1/delete",
                data={"living_expense_id": "10"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert len(living_items_uc.delete_item_calls) == 1
    assert living_items_uc.items[10] == []
    assert living_items_uc.receipts[10].amount.amount == 0
    assert "品目は登録されていません。" in response.text


# --- 9. POST /month/{y}/{m}/receipts/{id}/items/paste-preview ------------------------------


def test_paste_preview_shows_parsed_rows_without_saving(
    stubs: tuple[StubManageLivingExpensesUseCase, StubManageLivingExpenseItemsUseCase],
) -> None:
    """IT-LIV-14: 貼り付けテキストの解析結果（プレビュー、保存なし）が応答に含まれる（US-03 AC2/AC3）"""
    living_expenses_uc, living_items_uc = stubs
    living_items_uc.receipts[10] = LivingExpense(
        id=10,
        year_month=YearMonth(2026, 3),
        category=LIVING_EXPENSE_CATEGORY_FOOD,
        location="",
        amount=Money(0),
        note="",
    )
    living_items_uc.items[10] = []
    paste_text = "とうふ\t108\t食品\nラップ\t298\t生活用品"

    try:
        with _client(living_expenses_uc, living_items_uc) as client:
            response = client.post(
                "/month/2026/3/receipts/10/items/paste-preview",
                data={"paste_text": paste_text},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert "貼り付けプレビュー" in response.text
    assert "とうふ" in response.text
    assert "ラップ" in response.text
    # 保存は行われない
    assert living_items_uc.items[10] == []


def test_paste_preview_highlights_invalid_line(
    stubs: tuple[StubManageLivingExpensesUseCase, StubManageLivingExpenseItemsUseCase],
) -> None:
    """IT-LIV-15(異常系): 解析に失敗した行は行単位でエラー表示される"""
    living_expenses_uc, living_items_uc = stubs
    living_items_uc.receipts[10] = LivingExpense(
        id=10,
        year_month=YearMonth(2026, 3),
        category=LIVING_EXPENSE_CATEGORY_FOOD,
        location="",
        amount=Money(0),
        note="",
    )
    living_items_uc.items[10] = []
    paste_text = "とうふ\t不正な金額\t食品"

    try:
        with _client(living_expenses_uc, living_items_uc) as client:
            response = client.post(
                "/month/2026/3/receipts/10/items/paste-preview",
                data={"paste_text": paste_text},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert "金額は0以上の整数で入力してください" in response.text
    assert "border-red-400" in response.text


# --- 10. POST /month/{y}/{m}/receipts/{id}/items/paste-save (All-or-Nothing) ----------------


def test_paste_save_all_valid_lines_are_saved(
    stubs: tuple[StubManageLivingExpensesUseCase, StubManageLivingExpenseItemsUseCase],
) -> None:
    """IT-LIV-16: 全行正常なら一括保存が呼ばれる（US-03 AC4）"""
    living_expenses_uc, living_items_uc = stubs
    living_items_uc.receipts[10] = LivingExpense(
        id=10,
        year_month=YearMonth(2026, 3),
        category=LIVING_EXPENSE_CATEGORY_FOOD,
        location="",
        amount=Money(0),
        note="",
    )
    living_items_uc.items[10] = []

    try:
        with _client(living_expenses_uc, living_items_uc) as client:
            response = client.post(
                "/month/2026/3/receipts/10/items/paste-save",
                data={
                    "name": ["とうふ", "ラップ"],
                    "amount": ["108", "298"],
                    "sub_category": ["食品", "生活用品"],
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert len(living_items_uc.items[10]) == 2
    assert {i.name for i in living_items_uc.items[10]} == {"とうふ", "ラップ"}
    assert living_items_uc.receipts[10].amount.amount == 406
    assert "一部の行が想定形式" not in response.text


def test_paste_save_with_invalid_line_saves_nothing_all_or_nothing(
    stubs: tuple[StubManageLivingExpensesUseCase, StubManageLivingExpenseItemsUseCase],
) -> None:
    """IT-LIV-17: 1行でも不正な場合は保存されずエラー応答になる（US-03 AC5, All-or-Nothing）"""
    living_expenses_uc, living_items_uc = stubs
    living_items_uc.receipts[10] = LivingExpense(
        id=10,
        year_month=YearMonth(2026, 3),
        category=LIVING_EXPENSE_CATEGORY_FOOD,
        location="",
        amount=Money(0),
        note="",
    )
    living_items_uc.items[10] = []

    try:
        with _client(living_expenses_uc, living_items_uc) as client:
            response = client.post(
                "/month/2026/3/receipts/10/items/paste-save",
                data={
                    "name": ["とうふ", "不正行"],
                    "amount": ["108", "abc"],
                    "sub_category": ["食品", "生活用品"],
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    # All-or-Nothing: 1行目が正常でも1件も保存されない
    assert living_items_uc.items[10] == []
    assert living_items_uc.receipts[10].amount.amount == 0
    assert "一部の行が想定形式（品目名・金額・小分類）に一致しません。該当行を確認してください" in response.text


def test_paste_save_form_field_length_mismatch_is_rejected_without_saving(
    stubs: tuple[StubManageLivingExpensesUseCase, StubManageLivingExpenseItemsUseCase],
) -> None:
    """IT-LIV-18(異常系): name/amount/sub_categoryの送信件数が食い違う場合は保存せずエラー表示する"""
    living_expenses_uc, living_items_uc = stubs
    living_items_uc.receipts[10] = LivingExpense(
        id=10,
        year_month=YearMonth(2026, 3),
        category=LIVING_EXPENSE_CATEGORY_FOOD,
        location="",
        amount=Money(0),
        note="",
    )
    living_items_uc.items[10] = []

    try:
        with _client(living_expenses_uc, living_items_uc) as client:
            response = client.post(
                "/month/2026/3/receipts/10/items/paste-save",
                data={
                    "name": ["とうふ", "ラップ"],
                    "amount": ["108"],
                    "sub_category": ["食品", "生活用品"],
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert living_items_uc.items[10] == []
    assert "送信されたデータの形式が不正です" in response.text


# --- 既存の生活費簡易入力エンドポイントの回帰確認（変更していないもの） -------------------------


def test_regression_save_living_expense_still_works(
    stubs: tuple[StubManageLivingExpensesUseCase, StubManageLivingExpenseItemsUseCase],
) -> None:
    """IT-LIV-19(回帰): 既存の生活費簡易入力（追加）が本機能追加後も動作する"""
    living_expenses_uc, living_items_uc = stubs

    try:
        with _client(living_expenses_uc, living_items_uc) as client:
            response = client.post(
                "/month/2026/3/living-expenses",
                data={"category": "gas", "location": "", "amount": "4500", "note": ""},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert len(living_expenses_uc.add_calls) == 1
    assert "ガス代" in response.text
    assert "4,500円" in response.text


def test_regression_save_living_expense_food_requires_location(
    stubs: tuple[StubManageLivingExpensesUseCase, StubManageLivingExpenseItemsUseCase],
) -> None:
    """IT-LIV-20(回帰・異常系): 食費の簡易入力で場所が未入力ならエラーになる"""
    living_expenses_uc, living_items_uc = stubs
    living_expenses_uc.raise_on_add = ValueError("食費の場合は場所が必須です")

    try:
        with _client(living_expenses_uc, living_items_uc) as client:
            response = client.post(
                "/month/2026/3/living-expenses",
                data={"category": "food", "location": "", "amount": "1000", "note": ""},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert "食費の場合は場所が必須です" in response.text


def test_regression_update_and_delete_living_expense_still_work(
    stubs: tuple[StubManageLivingExpensesUseCase, StubManageLivingExpenseItemsUseCase],
) -> None:
    """IT-LIV-21(回帰): 既存の生活費簡易入力の更新・削除が本機能追加後も動作する"""
    living_expenses_uc, living_items_uc = stubs
    living_expenses_uc.expenses.append(
        LivingExpense(
            id=5,
            year_month=YearMonth(2026, 3),
            category="mobile",
            location="",
            amount=Money(6000),
            note="",
        )
    )

    try:
        with _client(living_expenses_uc, living_items_uc) as client:
            update_response = client.post(
                "/month/2026/3/living-expenses/5",
                data={"category": "mobile", "location": "", "amount": "6500", "note": ""},
            )
    finally:
        app.dependency_overrides.clear()

    assert update_response.status_code == 200
    assert len(living_expenses_uc.update_calls) == 1
    assert "6,500円" in update_response.text

    try:
        with _client(living_expenses_uc, living_items_uc) as client:
            delete_response = client.post("/month/2026/3/living-expenses/5/delete")
    finally:
        app.dependency_overrides.clear()

    assert delete_response.status_code == 200
    assert len(living_expenses_uc.delete_calls) == 1
    assert living_expenses_uc.expenses == []
