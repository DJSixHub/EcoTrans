from fastapi import APIRouter
from app.api.api_v1.endpoints import analytics, auth, incidents, search

api_router = APIRouter()
api_router.include_router(auth.router, tags=["auth"])
api_router.include_router(analytics.router, tags=["analytics"])
api_router.include_router(incidents.router, tags=["incidents"])
api_router.include_router(search.router, tags=["search"])
