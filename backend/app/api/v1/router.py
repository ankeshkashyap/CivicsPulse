from fastapi import APIRouter
from app.api.v1.endpoints import health, auth, complaints

api_router = APIRouter()

# Register endpoint sub-routers
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(auth.router, tags=["Authentication"])
api_router.include_router(complaints.router, prefix="/complaints", tags=["Complaints"])

