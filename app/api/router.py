from fastapi import APIRouter
from app.api.auth import router as auth_router
from app.api.organizations import router as org_router
from app.api.users import router as users_router
from app.api.plans import router as plans_router
from app.api.subscriptions import router as subs_router

router = APIRouter()

router.include_router(auth_router)
router.include_router(org_router)
router.include_router(users_router)
router.include_router(plans_router)
router.include_router(subs_router)

@router.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status": "OK"}