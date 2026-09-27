from fastapi import FastAPI
from app.api.router import router as api_router
from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
)

app.include_router(
    api_router, 
    prefix="/api"
)