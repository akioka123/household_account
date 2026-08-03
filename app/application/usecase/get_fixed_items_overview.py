"""固定費棚卸しユースケース"""

from __future__ import annotations

from dataclasses import dataclass

from app.application.port.card_repository import CardRepository
from app.application.port.fixed_item_history_repository import FixedItemHistoryRepository
from app.application.port.fixed_item_repository import FixedItemRepository
from app.application.port.logger import Logger
from app.domain.model.fixed_expenses import FixedExpenses
from app.domain.model.fixed_item_history import FixedItemHistory
from app.domain.model.log_context import LogContext
from app.domain.model.money import Money
from app.domain.model.year_month import YearMonth

MONTHS_PER_YEAR = 12
"""年額換算に使う月数"""


@dataclass(frozen=True)
class FixedItemHistoryView:
    """改定履歴の表示用データ"""

    effective_from: YearMonth
    """適用開始年月"""
    amount: Money
    """金額"""
    diff_from_previous: int | None
    """前回改定からの差額。初回はNone。減額の場合は負の値"""
    card_name: str | None
    """カード名（未紐づけ・削除済みカードの場合はNone）"""
    is_ended: bool
    """運用終了（金額0）かどうか"""


@dataclass(frozen=True)
class FixedItemOverview:
    """固定費項目1件の棚卸し表示用データ"""

    fixed_item_id: int
    """固定費項目ID"""
    name: str
    """項目名"""
    monthly_amount: Money
    """基準年月時点の月額（運用終了項目は0）"""
    annual_amount: Money
    """年額換算（月額×12）"""
    share_percent: float | None
    """月額合計に占める割合。合計が0の場合はNone"""
    card_name: str | None
    """カード名（未紐づけ・削除済みカードの場合はNone）"""
    included_in_card: bool
    """カード請求に含まれる固定費かどうか"""
    effective_from: YearMonth
    """現在の金額が適用された年月"""
    months_since_change: int
    """前回改定からの経過月数"""
    histories: list[FixedItemHistoryView]
    """全期間の改定履歴（適用開始年月の昇順）"""


@dataclass(frozen=True)
class FixedItemsOverview:
    """固定費棚卸し画面全体のデータ"""

    base_ym: YearMonth
    """基準年月"""
    active_items: list[FixedItemOverview]
    """有効な固定費（月額の降順、同額は項目名の昇順）"""
    ended_items: list[FixedItemOverview]
    """運用終了済みの固定費（終了年月の降順）"""
    monthly_total: Money
    """有効な固定費の月額合計"""
    annual_total: Money
    """有効な固定費の年額換算合計"""
    active_count: int
    """有効な固定費の件数"""


class GetFixedItemsOverviewUseCase:
    """固定費棚卸しユースケース

    基準年月時点で有効な固定費と、その改定履歴を一覧で取得する。
    リポジトリは全件取得を3回だけ行い、絞り込みと集計はメモリ上で処理する。
    """

    def __init__(
        self,
        fixed_item_repo: FixedItemRepository,
        fixed_item_history_repo: FixedItemHistoryRepository,
        card_repo: CardRepository,
        logger: Logger,
    ) -> None:
        self._fixed_item_repo = fixed_item_repo
        self._fixed_item_history_repo = fixed_item_history_repo
        self._card_repo = card_repo
        self._logger = logger

    async def execute(self, base_ym: YearMonth) -> FixedItemsOverview:
        """基準年月時点の固定費一覧を取得

        Args:
            base_ym: 基準年月

        Returns:
            固定費棚卸しデータ
        """
        fixed_items = await self._fixed_item_repo.find_all()
        all_histories = await self._fixed_item_history_repo.find_all()
        cards = await self._card_repo.find_all()

        names_by_item_id = {item.id: item.name for item in fixed_items}
        card_names_by_id = {card.id: card.name for card in cards}
        histories_by_item_id = self._group_histories(all_histories)

        # 基準年月時点で有効な履歴から、項目ごとの最新履歴を確定する
        active_at_base = [h for h in all_histories if h.is_active_at(base_ym)]
        effective_histories = FixedExpenses(active_at_base).get_effective_histories()

        # 割合の分母となる月額合計を先に確定する
        monthly_total = Money(0)
        for history in effective_histories:
            if not history.is_deleted():
                monthly_total = monthly_total + history.amount

        active_items: list[FixedItemOverview] = []
        ended_items: list[FixedItemOverview] = []
        for history in effective_histories:
            name = names_by_item_id.get(history.fixed_item_id)
            if name is None:
                # 項目マスタが存在しない履歴は表示対象外
                continue

            overview = self._build_overview(
                history=history,
                name=name,
                base_ym=base_ym,
                monthly_total=monthly_total,
                card_names_by_id=card_names_by_id,
                histories=histories_by_item_id.get(history.fixed_item_id, []),
            )
            if history.is_deleted():
                ended_items.append(overview)
            else:
                active_items.append(overview)

        # sortは安定なので、項目名昇順に並べてから主キーで並べ替える
        active_items.sort(key=lambda o: o.name)
        active_items.sort(key=lambda o: o.monthly_amount.amount, reverse=True)
        ended_items.sort(key=lambda o: o.name)
        ended_items.sort(key=lambda o: o.effective_from, reverse=True)

        context = LogContext(
            screen="fixed_items",
            context={"base_ym": base_ym.to_string(), "action": "get_fixed_items_overview"},
        )
        self._logger.info(
            f"固定費棚卸し取得: {base_ym.to_string()} (有効{len(active_items)}件)", context
        )

        return FixedItemsOverview(
            base_ym=base_ym,
            active_items=active_items,
            ended_items=ended_items,
            monthly_total=monthly_total,
            annual_total=monthly_total * MONTHS_PER_YEAR,
            active_count=len(active_items),
        )

    def _build_overview(
        self,
        history: FixedItemHistory,
        name: str,
        base_ym: YearMonth,
        monthly_total: Money,
        card_names_by_id: dict[int, str],
        histories: list[FixedItemHistory],
    ) -> FixedItemOverview:
        """固定費項目1件分の表示用データを組み立てる"""
        is_ended = history.is_deleted()
        monthly_amount = Money(0) if is_ended else history.amount

        share_percent: float | None = None
        if not is_ended and monthly_total.amount > 0:
            share_percent = monthly_amount.amount / monthly_total.amount * 100

        return FixedItemOverview(
            fixed_item_id=history.fixed_item_id,
            name=name,
            monthly_amount=monthly_amount,
            annual_amount=monthly_amount * MONTHS_PER_YEAR,
            share_percent=share_percent,
            card_name=self._resolve_card_name(history.card_id, card_names_by_id),
            included_in_card=history.included_in_card,
            effective_from=history.effective_from,
            months_since_change=self._months_between(history.effective_from, base_ym),
            histories=self._build_history_views(histories, card_names_by_id),
        )

    @classmethod
    def _build_history_views(
        cls,
        histories: list[FixedItemHistory],
        card_names_by_id: dict[int, str],
    ) -> list[FixedItemHistoryView]:
        """改定履歴に前回との差額を付けて表示用に変換する

        Moneyの減算は結果が負になると例外になるため、差額はintで計算する。
        """
        views: list[FixedItemHistoryView] = []
        previous: FixedItemHistory | None = None
        for history in histories:
            diff = None if previous is None else history.amount.amount - previous.amount.amount
            views.append(
                FixedItemHistoryView(
                    effective_from=history.effective_from,
                    amount=history.amount,
                    diff_from_previous=diff,
                    card_name=cls._resolve_card_name(history.card_id, card_names_by_id),
                    is_ended=history.is_deleted(),
                )
            )
            previous = history
        return views

    @staticmethod
    def _group_histories(
        histories: list[FixedItemHistory],
    ) -> dict[int, list[FixedItemHistory]]:
        """固定費項目IDごとに履歴をまとめ、適用開始年月の昇順に並べる"""
        grouped: dict[int, list[FixedItemHistory]] = {}
        for history in histories:
            grouped.setdefault(history.fixed_item_id, []).append(history)
        for item_histories in grouped.values():
            item_histories.sort(key=lambda h: h.effective_from)
        return grouped

    @staticmethod
    def _resolve_card_name(
        card_id: int | None, card_names_by_id: dict[int, str]
    ) -> str | None:
        """カードIDからカード名を解決する（未紐づけ・削除済みはNone）"""
        if card_id is None:
            return None
        return card_names_by_id.get(card_id)

    @staticmethod
    def _months_between(start: YearMonth, end: YearMonth) -> int:
        """2つの年月の間の月数を返す"""
        return (end.year - start.year) * MONTHS_PER_YEAR + (end.month - start.month)
