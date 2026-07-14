from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.jobs import router as jobs_router
from app.api.v1.applications import router as apps_router, jobs_applications_router

# Bundle all sub-routers together into a single API router
api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(jobs_router)
api_router.include_router(apps_router)
api_router.include_router(jobs_applications_router)
