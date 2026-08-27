"""receipt_paste_parser（parse_receipt_paste_text）のテスト

基本設計4.1.3節の判定規則5つを1つずつ検証する。
"""
from __future__ import annotations

from app.domain.model.living_expense_item import (
    LIVING_EXPENSE_ITEM_SUBCATEGORY_DAILY_GOODS,
    LIVING_EXPENSE_ITEM_SUBCATEGORY_GROCERY,
)
from app.domain.service.receipt_paste_parser import parse_receipt_paste_text


def test_rule1_blank_lines_are_ignored() -> None:
    """規則1: 空行は無視される（結果に含まれない）"""
    text = "牛乳\t200\t食品\n\n   \n石鹸\t300\t生活用品\n"

    results = parse_receipt_paste_text(text)

    assert len(results) == 2
    assert results[0].name == "牛乳"
    assert results[1].name == "石鹸"


def test_rule2_line_not_split_into_three_parts_is_error() -> None:
    """規則2: タブで3項目に一致しない行はエラー"""
    results = parse_receipt_paste_text("牛乳\t200")

    assert len(results) == 1
    assert results[0].error is not None
    assert results[0].name is None
    assert results[0].amount is None
    assert results[0].sub_category is None


def test_rule2_line_with_too_many_parts_is_error() -> None:
    """規則2: タブ区切りが4項目以上の行もエラー"""
    results = parse_receipt_paste_text("牛乳\t200\t食品\t余分")

    assert len(results) == 1
    assert results[0].error is not None


def test_rule3_amount_not_parseable_as_non_negative_int_is_error() -> None:
    """規則3: 金額が非負整数として解析できない行はエラー"""
    results = parse_receipt_paste_text("牛乳\t二百円\t食品")

    assert len(results) == 1
    assert results[0].error == "金額は0以上の整数で入力してください"


def test_rule3_negative_amount_is_error() -> None:
    """規則3: 金額が負の整数の行はエラー"""
    results = parse_receipt_paste_text("牛乳\t-100\t食品")

    assert len(results) == 1
    assert results[0].error == "金額は0以上の整数で入力してください"


def test_rule3_zero_amount_is_valid() -> None:
    """規則3の境界値: 金額0は有効な非負整数として解析される"""
    results = parse_receipt_paste_text("試供品\t0\t食品")

    assert len(results) == 1
    assert results[0].error is None
    assert results[0].amount == 0


def test_rule4_unknown_sub_category_label_is_error() -> None:
    """規則4: 小分類が固定リストのラベル（食品/生活用品）に一致しない行はエラー"""
    results = parse_receipt_paste_text("牛乳\t200\t飲料")

    assert len(results) == 1
    assert results[0].error == "小分類は食品または生活用品のいずれかを指定してください"


def test_rule5_empty_item_name_is_error() -> None:
    """規則5: 品目名が空文字の行はエラー"""
    results = parse_receipt_paste_text("\t200\t食品")

    assert len(results) == 1
    assert results[0].error == "品目名を入力してください"


def test_rule5_blank_item_name_is_error() -> None:
    """規則5: 品目名が空白のみの行もエラー（stripして判定される）"""
    results = parse_receipt_paste_text("   \t200\t食品")

    assert len(results) == 1
    assert results[0].error == "品目名を入力してください"


def test_multiple_normal_lines_are_parsed_correctly() -> None:
    """複数行の正常系: 食品・生活用品混在の3行が正しくパースされる"""
    text = "牛乳\t200\t食品\n石鹸\t300\t生活用品\nパン\t150\t食品"

    results = parse_receipt_paste_text(text)

    assert len(results) == 3
    assert [r.error for r in results] == [None, None, None]

    assert results[0].name == "牛乳"
    assert results[0].amount == 200
    assert results[0].sub_category == LIVING_EXPENSE_ITEM_SUBCATEGORY_GROCERY

    assert results[1].name == "石鹸"
    assert results[1].amount == 300
    assert results[1].sub_category == LIVING_EXPENSE_ITEM_SUBCATEGORY_DAILY_GOODS

    assert results[2].name == "パン"
    assert results[2].amount == 150
    assert results[2].sub_category == LIVING_EXPENSE_ITEM_SUBCATEGORY_GROCERY


def test_error_line_does_not_affect_other_normal_lines() -> None:
    """正常行とエラー行が混在する入力で、1行のエラーが他行に影響しない"""
    text = "牛乳\t200\t食品\n不正行\t二百円\t食品\n石鹸\t300\t生活用品"

    results = parse_receipt_paste_text(text)

    assert len(results) == 3
    assert results[0].error is None
    assert results[0].name == "牛乳"

    assert results[1].error == "金額は0以上の整数で入力してください"

    assert results[2].error is None
    assert results[2].name == "石鹸"
