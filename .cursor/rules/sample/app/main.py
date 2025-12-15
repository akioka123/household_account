from __future__ import annotations

from fastapi import FastAPI
from app.presentation.web.router import router

app = FastAPI()
app.include_router(router)
