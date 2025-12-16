"""現金管理ユースケース"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from app.application.port.cash_balance_repository import CashBalanceRepository
from app.application.port.logger import Logger
from app.application.port.withdrawal_repository import WithdrawalRepository
from app.domain.model.cash_balance import CashBalance
from app.domain.model.log_context import LogContext
from app.domain.model.money import Money
from app.domain.model.withdrawal import Withdrawal
from app.domain.model.year_month import YearMonth


@dataclass(frozen=True)
class UpdateCashBalanceCommand:
    """月初現金更新コマンド"""

    year: int
    """年"""
    month: int
    """月"""
    amount: int
    """月初現金"""


@dataclass(frozen=True)
class AddWithdrawalCommand:
    """引出明細追加コマンド"""

    year: int
    """年"""
    month: int
    """月"""
    withdrawal_date: date
    """引出日付"""
    amount: int
    """引出金額"""
    note: str
    """メモ"""


@dataclass(frozen=True)
class DeleteWithdrawalCommand:
    """引出明細削除コマンド"""

    withdrawal_id: int
    """引出明細ID"""


@dataclass(frozen=True)
class CashData:
    """現金データ（表示用）"""

    cash_start: CashBalance | None
    """月初現金"""
    withdrawals: list[Withdrawal]
    """引出明細"""
    cash_start_next: CashBalance | None
    """次月月初現金"""


class ManageCashUseCase:
    """現金管理ユースケース"""

    def __init__(
        self,
        cash_balance_repo: CashBalanceRepository,
        withdrawal_repo: WithdrawalRepository,
        logger: Logger,
    ) -> None:
        self._cash_balance_repo = cash_balance_repo
        self._withdrawal_repo = withdrawal_repo
        self._logger = logger

    async def update_cash_balance(self, command: UpdateCashBalanceCommand) -> None:
        """月初現金を更新

        Args:
            command: 月初現金更新コマンド
        """
        ym = YearMonth(command.year, command.month)

        # 既存の月初現金を取得
        existing = await self._cash_balance_repo.find(ym)

        if existing:
            # 更新
            balance = CashBalance(
                id=existing.id,
                year_month=ym,
                amount=Money(command.amount),
            )
        else:
            # 新規作成：最大IDを取得して次のIDを決定
            all_balances = await self._cash_balance_repo.find_all()
            next_id = max([b.id for b in all_balances], default=0) + 1
            balance = CashBalance(
                id=next_id,
                year_month=ym,
                amount=Money(command.amount),
            )

        await self._cash_balance_repo.save(balance)

        context = LogContext(
            screen="month",
            context={
                "year": command.year,
                "month": command.month,
                "action": "update_cash_balance",
            },
        )
        self._logger.info(
            f"月初現金更新: {command.year}年{command.month}月 ({command.amount}円)", context
        )

    async def add_withdrawal(self, command: AddWithdrawalCommand) -> None:
        """引出明細を追加

        Args:
            command: 引出明細追加コマンド
        """
        ym = YearMonth(command.year, command.month)

        # 最大IDを取得して次のIDを決定（全データから取得してグローバルな一意性を保証）
        all_withdrawals = await self._withdrawal_repo.find_all()
        next_id = max([w.id for w in all_withdrawals], default=0) + 1

        withdrawal = Withdrawal(
            id=next_id,
            year_month=ym,
            withdrawal_date=command.withdrawal_date,
            amount=Money(command.amount),
            note=command.note,
        )

        await self._withdrawal_repo.save(withdrawal)

        context = LogContext(
            screen="month",
            context={
                "year": command.year,
                "month": command.month,
                "action": "add_withdrawal",
            },
        )
        self._logger.info(
            f"引出明細追加: {command.year}年{command.month}月 ({command.amount}円)", context
        )

    async def delete_withdrawal(self, command: DeleteWithdrawalCommand) -> None:
        """引出明細を削除

        Args:
            command: 引出明細削除コマンド
        """
        await self._withdrawal_repo.delete(command.withdrawal_id)

        context = LogContext(
            screen="month",
            context={"action": "delete_withdrawal", "withdrawal_id": command.withdrawal_id},
        )
        self._logger.info(f"引出明細削除: ID {command.withdrawal_id}", context)

    async def get_cash_data(self, year: int, month: int) -> CashData:
        """現金データを取得

        Args:
            year: 年
            month: 月

        Returns:
            現金データ
        """
        ym = YearMonth(year, month)
        next_ym = YearMonth(year, month + 1) if month < 12 else YearMonth(year + 1, 1)

        cash_start = await self._cash_balance_repo.find(ym)
        withdrawals = await self._withdrawal_repo.find_by_year_month(ym)
        cash_start_next = await self._cash_balance_repo.find(next_ym)

        return CashData(
            cash_start=cash_start,
            withdrawals=withdrawals,
            cash_start_next=cash_start_next,
        )
