"""カード管理ユースケース"""
from __future__ import annotations

from dataclasses import dataclass

from app.application.port.card_repository import CardRepository
from app.application.port.logger import Logger
from app.domain.model.card import Card
from app.domain.model.log_context import LogContext


@dataclass(frozen=True)
class CreateCardCommand:
    """カード作成コマンド"""

    name: str


@dataclass(frozen=True)
class UpdateCardCommand:
    """カード更新コマンド"""

    card_id: int
    name: str | None = None
    enabled: bool | None = None


class ManageCardsUseCase:
    """カード管理ユースケース"""

    def __init__(self, card_repo: CardRepository, logger: Logger) -> None:
        self._card_repo = card_repo
        self._logger = logger

    async def create_card(self, command: CreateCardCommand) -> Card:
        """カードを作成"""
        # 最大IDを取得して次のIDを決定（簡易実装）
        all_cards = await self._card_repo.find_all()
        next_id = max([c.id for c in all_cards], default=0) + 1

        card = Card(id=next_id, name=command.name, enabled=True)
        await self._card_repo.save(card)

        context = LogContext(screen="settings", context={"card_id": card.id, "action": "create"})
        self._logger.info(f"カード作成: {card.name}", context)

        return card

    async def update_card(self, command: UpdateCardCommand) -> Card:
        """カードを更新"""
        card = await self._card_repo.find_by_id(command.card_id)
        if card is None:
            raise ValueError(f"Card not found: {command.card_id}")

        updated = card
        if command.name is not None:
            updated = updated.rename(command.name)
        if command.enabled is not None:
            updated = updated.enable() if command.enabled else updated.disable()

        await self._card_repo.save(updated)

        context = LogContext(
            screen="settings", context={"card_id": card.id, "action": "update"}
        )
        self._logger.info(f"カード更新: {updated.name}", context)

        return updated

    async def get_all_cards(self) -> list[Card]:
        """全カードを取得"""
        return await self._card_repo.find_all()
