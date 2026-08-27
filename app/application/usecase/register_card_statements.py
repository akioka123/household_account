"""カード請求登録ユースケース"""
from __future__ import annotations

from dataclasses import dataclass

from app.application.port.card_repository import CardRepository
from app.application.port.card_statement_repository import CardStatementRepository
from app.application.port.logger import Logger
from app.application.port.settings_repository import SettingsRepository
from app.domain.model.card_statement import CardStatement
from app.domain.model.log_context import LogContext
from app.domain.model.money import Money
from app.domain.model.year_month import YearMonth


@dataclass(frozen=True)
class CardStatementCommand:
    """カード請求コマンド"""

    card_id: int
    """カードID"""
    amount: int
    """請求総額"""


class RegisterCardStatementsUseCase:
    """カード請求登録ユースケース"""

    def __init__(
        self,
        card_statement_repo: CardStatementRepository,
        card_repo: CardRepository,
        settings_repo: SettingsRepository,
        logger: Logger,
    ) -> None:
        self._card_statement_repo = card_statement_repo
        self._card_repo = card_repo
        self._settings_repo = settings_repo
        self._logger = logger

    async def execute(
        self, year: int, month: int, commands: list[CardStatementCommand]
    ) -> None:
        """カード請求を登録または更新

        Args:
            year: 年
            month: 月
            commands: カード請求コマンドのリスト

        Raises:
            ValueError: カードが見つからない場合、または行数が上限を超える場合
        """
        settings = await self._settings_repo.find()
        if len(commands) > settings.max_variable_items:
            raise ValueError(
                f"変動費の登録件数が上限（{settings.max_variable_items}件）を超えています"
            )

        ym = YearMonth(year, month)

        # 既存のカード請求を取得
        existing_statements = await self._card_statement_repo.find_by_year_month(ym)
        existing_by_card_id = {stmt.card_id: stmt for stmt in existing_statements}

        # 最大IDを取得して次のIDを決定（全データから取得してグローバルな一意性を保証）
        all_statements = await self._card_statement_repo.find_all()
        max_id = max([stmt.id for stmt in all_statements], default=0)
        next_id = max_id + 1

        # 各コマンドを処理
        for cmd in commands:
            # カードの存在確認
            card = await self._card_repo.find_by_id(cmd.card_id)
            if card is None:
                raise ValueError(f"Card not found: {cmd.card_id}")

            # 既存の請求がある場合は更新、ない場合は新規作成
            existing = existing_by_card_id.get(cmd.card_id)
            if existing:
                # 更新（新しいインスタンスを作成）
                statement = CardStatement(
                    id=existing.id,
                    year_month=ym,
                    card_id=cmd.card_id,
                    amount=Money(cmd.amount),
                )
            else:
                # 新規作成
                statement = CardStatement(
                    id=next_id,
                    year_month=ym,
                    card_id=cmd.card_id,
                    amount=Money(cmd.amount),
                )
                next_id += 1

            await self._card_statement_repo.save(statement)

        # ログ出力
        context = LogContext(
            screen="month",
            context={
                "year": year,
                "month": month,
                "action": "register_card_statements",
                "count": len(commands),
            },
        )
        self._logger.info(
            f"カード請求登録: {year}年{month}月 ({len(commands)}件)", context
        )

