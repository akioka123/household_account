"""収入のエンティティ"""
from __future__ import annotations

from dataclasses import dataclass

from app.domain.model.money import Money


@dataclass(frozen=True)
class Income:
    """当月の収入（給与/賞与）"""

    salary_gross: Money
    """給与額面"""
    salary_net: Money
    """給与手取り"""
    bonus_gross: Money
    """賞与額面"""
    bonus_net: Money
    """賞与手取り"""

    @staticmethod
    def of(
        salary_gross: int,
        salary_net: int,
        bonus_gross: int,
        bonus_net: int,
    ) -> Income:
        """ファクトリメソッド"""
        return Income(
            salary_gross=Money(salary_gross),
            salary_net=Money(salary_net),
            bonus_gross=Money(bonus_gross),
            bonus_net=Money(bonus_net),
        )

    def net_total(self) -> Money:
        """手取り合計を計算"""
        return self.salary_net + self.bonus_net

    def gross_total(self) -> Money:
        """額面合計を計算"""
        return self.salary_gross + self.bonus_gross
