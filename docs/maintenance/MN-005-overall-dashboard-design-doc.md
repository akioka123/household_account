# MN-005: 総合ダッシュボード画面が基本設計書に未記載

## 事象

- 再現手順: `docs/basic_design.md` の画面構成設計（2章）を確認する
- 期待結果: 実装済みの全画面（`/dashboard/{year}`, `/month/{year}/{month}`, `/settings`, `/fixed-items`, `/dashboard/overall`）が記載されている
- 実際の結果: `/dashboard/overall`（総合ダッシュボード、`app/presentation/web/routers/dashboard_router.py`、`app/application/usecase/get_overall_dashboard_data.py`）が一切記載されておらず、設計書と実装が乖離していた

## 原因

- 実装追加時に基本設計書への反映が漏れていた（コード変更のみ、ドキュメント側の追記なし）

## 方針

- ユーザー承認: 2026-08-27
- 既存の画面セクション（2.1〜2.5）の番号は変更せず、末尾に「2.6 総合ダッシュボード画面」を追記する

## 修正

- `docs/basic_design.md`: 「2.6 総合ダッシュボード画面 `/dashboard/overall`」を新設。実装（`GetOverallDashboardDataUseCase`, `dashboard/overall.html`, `overall-dashboard-chart.js`）を読んで、表示項目・算出方法・htmx方針を既存セクション（2.5）と同じ粒度で記載

## ミニ検証

- コード変更なし（ドキュメントのみ）のため `ruff`/`pytest` は対象外
- 目視確認: 実装（ルーター・ユースケース・テンプレート）と記載内容の突合を実施

## 影響範囲

- `docs/basic_design.md`
