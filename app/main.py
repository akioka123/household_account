"""FastAPIアプリケーションのエントリーポイント"""
from __future__ import annotations

from datetime import datetime

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.infrastructure.middleware.access_log import AccessLogMiddleware
from app.presentation.web.routers.dashboard_router import router as dashboard_router
from app.presentation.web.routers.month_router import router as month_router
from app.presentation.web.routers.settings_router import router as settings_router

app = FastAPI(
    title="家計簿ダッシュボード",
    description="月次損益と年次推移を可視化するローカルアプリ",
    version="0.1.0",
)

# アクセスログミドルウェアを追加
app.add_middleware(AccessLogMiddleware)

# Jinja2テンプレートエンジン設定
templates = Jinja2Templates(directory="app/presentation/templates")

# ルーターを登録
app.include_router(dashboard_router)
app.include_router(settings_router)
app.include_router(month_router)


@app.get("/")
async def root() -> RedirectResponse:
    """ルートエンドポイント：現在年のダッシュボードにリダイレクト"""
    current_year = datetime.now().year
    return RedirectResponse(url=f"/dashboard/{current_year}")
