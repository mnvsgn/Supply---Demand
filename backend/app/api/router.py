from fastapi import APIRouter
from app.api.routes import datasets, health, sessions, upload, chat, forecasts, admin

api_router = APIRouter()
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(sessions.router)
api_router.include_router(upload.router)
api_router.include_router(chat.router)
api_router.include_router(forecasts.router)
api_router.include_router(datasets.router)
api_router.include_router(admin.router)
