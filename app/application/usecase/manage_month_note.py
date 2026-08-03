"""月次メモ管理ユースケース"""
from __future__ import annotations

from dataclasses import dataclass

from app.application.port.logger import Logger
from app.application.port.month_note_repository import MonthNoteRepository
from app.domain.model.log_context import LogContext
from app.domain.model.month_note import MonthNote
from app.domain.model.year_month import YearMonth


@dataclass(frozen=True)
class SaveMonthNoteCommand:
    """月次メモ保存コマンド"""

    year: int
    """対象年"""
    month: int
    """対象月"""
    note: str
    """メモ本文（空文字の場合は削除扱い）"""


class ManageMonthNoteUseCase:
    """月次メモ管理ユースケース"""

    def __init__(
        self,
        month_note_repo: MonthNoteRepository,
        logger: Logger,
    ) -> None:
        self._month_note_repo = month_note_repo
        self._logger = logger

    async def get_note(self, year: int, month: int) -> MonthNote | None:
        """指定年月の月次メモを取得

        Args:
            year: 対象年
            month: 対象月

        Returns:
            月次メモ（未登録の場合はNone）
        """
        return await self._month_note_repo.find(YearMonth(year, month))

    async def get_notes_by_year(self, year: int) -> dict[YearMonth, MonthNote]:
        """指定年の月次メモを年月をキーにして取得

        Args:
            year: 対象年

        Returns:
            年月をキーとした月次メモの辞書
        """
        return await self._month_note_repo.find_by_year(year)

    async def save_note(self, command: SaveMonthNoteCommand) -> MonthNote | None:
        """月次メモを保存（空文字の場合は削除）

        Args:
            command: 月次メモ保存コマンド

        Returns:
            保存後の月次メモ（削除した場合はNone）

        Raises:
            ValueError: メモが最大文字数を超える場合
        """
        ym = YearMonth(command.year, command.month)
        context = LogContext(screen="month", context={"year": command.year, "month": command.month})

        note = MonthNote.of(ym, command.note)

        if note.is_empty():
            await self._month_note_repo.delete(ym)
            self._logger.info(f"月次メモ削除: {ym.to_string()}", context)
            return None

        await self._month_note_repo.save(note)
        self._logger.info(f"月次メモ保存: {ym.to_string()}", context)
        return await self._month_note_repo.find(ym)
