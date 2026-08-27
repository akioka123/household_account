# 家計簿ダッシュボード

月次損益と年次推移を可視化するローカルアプリケーション

## クイックスタート

### 前提条件

- Docker と Docker Compose がインストールされていること

### 起動手順

1. **リポジトリをクローン（またはダウンロード）**

```bash
cd household_account
```

2. **環境変数の設定（オプション）**

必要に応じて、`.env`ファイルを作成してデータベースパスワードを設定できます：

```bash
DB_PASSWORD=your_password_here
LOG_LEVEL=INFO
```

設定しない場合は、デフォルト値（`DB_PASSWORD=secret`）が使用されます。

3. **アプリケーションの起動**

```bash
docker-compose up -d
```

初回起動時は、Dockerイメージのビルドとデータベースの初期化に時間がかかります。

4. **データベースマイグレーションの実行**

アプリケーションコンテナ内でマイグレーションを実行します：

```bash
docker-compose exec app alembic upgrade head
```

5. **アプリケーションへのアクセス**

ブラウザで以下のURLにアクセスしてください：

```
http://localhost:8000
```

ルート（`/`）にアクセスすると、現在年のダッシュボード（`/dashboard/{現在年}`）にリダイレクトされます。

### 停止方法

```bash
docker-compose down
```

データを保持したまま停止する場合は上記のコマンド、データも削除する場合は：

```bash
docker-compose down -v
```

### ログの確認

```bash
# すべてのサービスのログを確認
docker-compose logs -f

# アプリケーションのログのみ確認
docker-compose logs -f app

# データベースのログのみ確認
docker-compose logs -f db
```

### よくある操作

#### データベースマイグレーション

```bash
# 最新のマイグレーションを適用
docker-compose exec app alembic upgrade head

# マイグレーション履歴を確認
docker-compose exec app alembic history

# 1つ前のマイグレーションに戻す
docker-compose exec app alembic downgrade -1
```

#### コンテナの再起動

```bash
# すべてのコンテナを再起動
docker-compose restart

# アプリケーションコンテナのみ再起動
docker-compose restart app
```

#### アプリケーションの再ビルド

コードを変更した後、イメージを再ビルドする場合：

```bash
docker-compose up -d --build
```

## 技術スタック

- **バックエンド**: Python 3.12 / FastAPI
- **フロントエンド**: HTML テンプレート + htmx
- **データベース**: PostgreSQL 16
- **マイグレーション**: Alembic

## ポート

- **アプリケーション**: `8000`
- **データベース**: `5432`

## トラブルシューティング

### ポートが既に使用されている場合

`8000`ポートまたは`5432`ポートが既に使用されている場合は、`docker-compose.yml`の`ports`設定を変更してください。

### データベース接続エラー

データベースコンテナが正常に起動しているか確認してください：

```bash
docker-compose ps
```

データベースコンテナのログを確認：

```bash
docker-compose logs db
```

### マイグレーションエラー

マイグレーションが失敗した場合、データベースの状態を確認：

```bash
docker-compose exec app alembic current
```

必要に応じて、データベースをリセット：

```bash
docker-compose down -v
docker-compose up -d
docker-compose exec app alembic upgrade head
```

## 詳細情報

詳細な設計情報については、`docs/basic_design.md`を参照してください。
