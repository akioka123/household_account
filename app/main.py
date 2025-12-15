"""FastAPIアプリケーションのエントリーポイント"""
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.base import BaseHTTPMiddleware

from app.infrastructure.middleware.access_log import AccessLogMiddleware

app = FastAPI(
    title="家計簿ダッシュボード",
    description="月次損益と年次推移を可視化するローカルアプリ",
    version="0.1.0",
)

# アクセスログミドルウェアを追加
app.add_middleware(AccessLogMiddleware)

# Jinja2テンプレートエンジン設定
templates = Jinja2Templates(directory="app/presentation/templates")


@app.get("/", response_class=HTMLResponse)
async def root() -> str:
    """ルートエンドポイント（暫定）"""
    return """
    <html>
        <head><title>家計簿ダッシュボード</title></head>
        <body>
            <h1>家計簿ダッシュボード</h1>
            <p>アプリケーションが正常に起動しました。</p>
        </body>
    </html>
    """
