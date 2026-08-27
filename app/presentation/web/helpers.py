"""テンプレートヘルパー関数"""
from __future__ import annotations

from typing import Any


def get_years_with_data(
    current_year: int, years_with_data: set[int] | None = None
) -> list[dict[str, Any]]:
    """年選択ドロップダウン用の年リストを生成
    
    Args:
        current_year: 現在の年
        years_with_data: データが登録されている年のセット
    
    Returns:
        年情報のリスト（value, selected, has_dataを含む）
    """
    if years_with_data is None:
        years_with_data = set()
    
    # 現在年±5年の範囲を生成
    years = []
    for year in range(current_year - 5, current_year + 6):
        years.append({
            "value": year,
            "selected": year == current_year,
            "has_data": year in years_with_data,
        })
    
    return years
