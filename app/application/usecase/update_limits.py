"""上限設定更新ユースケース"""
from __future__ import annotations

from dataclasses import dataclass

from app.application.port.logger import Logger
from app.application.port.settings_repository import SettingsRepository
from app.domain.model.log_context import LogContext
from app.domain.model.settings import Settings


@dataclass(frozen=True)
class UpdateLimitsCommand:
    """上限設定更新コマンド"""

    max_variable_items: int | None = None
    max_fixed_items: int | None = None


class UpdateLimitsUseCase:
    """上限設定更新ユースケース"""

    def __init__(self, settings_repo: SettingsRepository, logger: Logger) -> None:
        self._settings_repo = settings_repo
        self._logger = logger

    async def execute(self, command: UpdateLimitsCommand) -> Settings:
        """上限設定を更新"""
        current_settings = await self._settings_repo.find()

        updated_settings = current_settings.update_limits(
            max_variable_items=command.max_variable_items,
            max_fixed_items=command.max_fixed_items,
        )

        await self._settings_repo.save(updated_settings)

        context = LogContext(screen="settings", context={"action": "update_limits"})
        self._logger.info(
            f"上限設定更新: 変動費={updated_settings.max_variable_items}, "
            f"固定費={updated_settings.max_fixed_items}",
            context,
        )

        return updated_settings
