from fastapi import APIRouter

from app.routers import admin, ai, analytics, categories, notifications, reports, statuses, users

api_router = APIRouter()

# Public / user-facing routers
api_router.include_router(users.router)
api_router.include_router(reports.router)
api_router.include_router(ai.router)
api_router.include_router(categories.router)
api_router.include_router(statuses.router)
api_router.include_router(notifications.router)

# Admin-only routers
api_router.include_router(admin.router)
api_router.include_router(analytics.router)