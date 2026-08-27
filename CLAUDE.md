# household_account（家計簿ダッシュボード）

## 概要

月次の損益と年次推移を可視化する個人用のローカルアプリ。収入・固定費・変動費（カード請求／現金）・生活費を月単位で登録し、年次ダッシュボードで推移とCSV出力を得る。個人利用のため収益化はしない。

## 制約

- 運用形態: ローカルのみ（Docker Compose）。外部公開・リモートpushはしない
- コスト上限: 未定義（企画書なし。金銭支出が発生する変更を行う前にユーザー確認）
- 技術方針: Python 3.12 / FastAPI / Jinja2 + htmx / Tailwind（CDN） / PostgreSQL（asyncpg） / SQLAlchemy 2.0 / Alembic

## 工程

グローバルルールの工程ゲート制に従う。基本設計は `docs/basic_design.md`、証跡は `docs/evidence/`。
`docs/gates/gate-status.md` は未整備（現状は実装・テストを反復中）。

hotfix-flow でバグ修正に着手する際、原因調査が採番方式の変更やスキーマ変更など設計判断を伴う場合は、
着手前に `docs/incidents/` へADR（フロントマター付き、規約は `docs/incidents/CLAUDE.md` 参照）を
作成してから修正する。単純な文言修正など決定を伴わない軽微な修正は対象外（hotfix-flow の
`docs/maintenance/MN-*.md` のみでよい）。

## アーキテクチャ

4層構成。依存は外側→内側の一方向のみ（presentation → application → domain、infrastructure → application/domain）。

```
app/
├── domain/model/          … エンティティ・値オブジェクト（frozen dataclass）
├── domain/service/        … 計算ロジック（MonthCalculator。データ取得はしない）
├── application/port/      … リポジトリの Protocol（インターフェース）
├── application/usecase/   … ユースケース。入力は <動詞>Command の frozen dataclass
├── infrastructure/        … SQLAlchemy モデル・リポジトリ実装・ロガー
└── presentation/          … FastAPI ルーター・Jinja2 テンプレート・静的JS
```

- Port は `app/application/port/` に `Protocol` で定義し、実装は `SqlAlchemy<名前>Repository`
- ルーターの DI は `provide_<名前>` 関数 + `Annotated[..., Depends(...)]`
- 表示用の整形（CSV生成など）は presentation 層に置く（例: `app/presentation/web/csv_export.py`）

## ドメイン用語と計算式

**この定義を取り違えると数値が静かに狂うため、変更前に必ず確認する。**

| 用語 | 定義 |
|---|---|
| 手取り収入 | `salary_net + bonus_net` |
| 固定費合計 | 当月時点で有効な固定費履歴の合計 |
| **カード変動費** | **カード請求総額 − カードに含まれる固定費**。カード請求総額そのものではない |
| 現金支出 | 月初現金 + 引出合計 − 次月月初現金 |
| 変動費合計 | カード変動費 + 現金支出 |
| 損益 | 手取り収入 − 固定費 − 変動費 |
| 生活費 | 食費 / 電気代 / ガス代 / 携帯料金 / 通信費。変動費とは別集計で、損益計算には含まない |

- `Money` は減算結果が負になると例外。損益など負を持ちうる値は `Money(int)` を直接生成する
- `YearMonth` は 1900〜9999 年・1〜12 月を検証する値オブジェクト。DB へは `YYYY-MM` 文字列で保存
- 次月月初現金が未登録の月は現金支出が未確定。警告を出し、表示用に「月初現金 + 引出」を使う

## 開発コマンド

```bash
docker compose up -d
```

- アプリ: http://localhost:8000 （`household-app`。`.:/app` マウント + `--reload` でソース変更は即反映）
- DB: `household-db` / `postgresql+asyncpg://household:secret@localhost:5432/household`
- マイグレーション: コンテナ起動時に `alembic upgrade head` が自動実行される

テストは同梱の venv で実行する（グローバルの python ではない）。

```bash
./venv/Scripts/python.exe -m pytest tests -q
```

- Lint: `./venv/Scripts/python.exe -m ruff check app tests`（line-length 100）
- 新しいマイグレーションは `alembic/versions/<3桁連番>_<説明>.py`。`revision` は `'009'` のようにゼロ埋め3桁の文字列

## 実装の約束

- docstring・コメント・UI文言はすべて日本語
- ドメインモデルは `@dataclass(frozen=True)`。不変条件は `__post_init__` で検証する
- 単体テストは `MagicMock(spec=<Port>)` + `AsyncMock` でリポジトリを差し替える（`asyncio_mode = auto` のため `@pytest.mark.asyncio` は任意）
- 結合テストは `TestClient` + `app.dependency_overrides` でユースケースを差し替え、DB なしで動かす
- 画面テンプレートを変更したら、実際に配信された HTML で確認する（後述）

## この環境での注意

- **テンプレート単体をブラウザで開かない**。`app/presentation/templates/**.html` は `{% extends %}` の断片で `<head>` を持たないため、直接開くと CSS が効かず未展開の `{{ }}` が見える。必ず起動中のアプリ（:8000）で確認する
- Browser ペインから localhost を開くには `.claude/launch.json`（起動中サーバへの attach 設定）を使う。直接 navigate はポリシーで拒否される
- コンソールが cp932 のため、日本語を出す Python ワンライナーは `PYTHONIOENCODING=utf-8` を付ける
- `node_modules/` は jsdom によるフロントJS検証用。`package.json` は無く、アプリの実行には不要
- 静的JS（`app/presentation/static/js/`）はブラウザにキャッシュされる。変更が反映されない場合はスーパーリロードを案内する
