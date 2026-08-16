from fastapi import APIRouter

from app.api import admin, auth, dashboards, datasets, insights, query, workspaces

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(workspaces.router)
api_router.include_router(datasets.router)
api_router.include_router(query.router)
api_router.include_router(insights.router)
api_router.include_router(dashboards.router)
api_router.include_router(admin.router)
