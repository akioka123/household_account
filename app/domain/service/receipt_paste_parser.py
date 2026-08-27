"""レシート貼り付けテキストの解析（純関数、データ取得は行わない）"""
from __future__ import annotations

from dataclasses import dataclass

from app.domain.model.living_expense_item import LIVING_EXPENSE_ITEM_SUBCATEGORY_LABELS

# 小分類ラベル（日本語表示）→ 内部値 の対応（LIVING_EXPENSE_ITEM_SUBCATEGORY_LABELSの逆引き）
_SUBCATEGORY_LABEL_TO_VALUE: dict[str, str] = {
    label: value for value, label in LIVING_EXPENSE_ITEM_SUBCATEGORY_LABELS.items()
}


@dataclass(frozen=True)
class ParsedReceiptLine:
    """貼り付けテキスト1行の解析結果"""

    raw_line: str
    """元の行文字列"""
    name: str | None
    """品目名（解析成功時のみ設定）"""
    amount: int | None
    """金額（解析成功時のみ設定）"""
    sub_category: str | None
    """小分類の内部値（解析成功時のみ設定）"""
    error: str | None
    """エラーメッセージ（解析失敗時のみ設定）"""


def parse_receipt_paste_text(text: str) -> list[ParsedReceiptLine]:
    """貼り付けテキスト（TSV、1行1品目、列順「品目名・金額・小分類」）を解析する

    判定規則（基本設計4.1.3節）:
        1. 空行は無視する（結果に含めない）
        2. タブで分割して3項目に一致しない行はエラー
        3. 金額が非負整数として解析できない行はエラー
        4. 小分類が固定リストのラベル（「食品」「生活用品」）に一致しない行はエラー
        5. 品目名が空文字の行はエラー

    Args:
        text: 貼り付けテキスト

    Returns:
        行ごとの解析結果のリスト（空行を除く）
    """
    results: list[ParsedReceiptLine] = []

    for raw_line in text.splitlines():
        if not raw_line.strip():
            # 規則1: 空行は無視する
            continue

        parts = raw_line.split("\t")
        if len(parts) != 3:
            results.append(
                _error_line(raw_line, "想定形式（品目名\t金額\t小分類）に一致しません")
            )
            continue

        name_part, amount_part, sub_category_label = parts

        amount_value = _parse_non_negative_int(amount_part.strip())
        if amount_value is None:
            results.append(_error_line(raw_line, "金額は0以上の整数で入力してください"))
            continue

        sub_category_value = _SUBCATEGORY_LABEL_TO_VALUE.get(sub_category_label.strip())
        if sub_category_value is None:
            results.append(
                _error_line(raw_line, "小分類は食品または生活用品のいずれかを指定してください")
            )
            continue

        name_value = name_part.strip()
        if not name_value:
            results.append(_error_line(raw_line, "品目名を入力してください"))
            continue

        results.append(
            ParsedReceiptLine(
                raw_line=raw_line,
                name=name_value,
                amount=amount_value,
                sub_category=sub_category_value,
                error=None,
            )
        )

    return results


def _parse_non_negative_int(text: str) -> int | None:
    """文字列を0以上の整数として解析する（解析できない場合はNone）"""
    try:
        value = int(text)
    except ValueError:
        return None
    if value < 0:
        return None
    return value


def _error_line(raw_line: str, error: str) -> ParsedReceiptLine:
    """エラー行を生成する"""
    return ParsedReceiptLine(
        raw_line=raw_line,
        name=None,
        amount=None,
        sub_category=None,
        error=error,
    )
