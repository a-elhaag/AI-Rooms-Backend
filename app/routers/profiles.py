from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db import get_database
from app.schemas.profile import ProfileOut, ProfileUpdate
from app.services.profile_service import ProfileService
from app.utils.security import get_current_user_id

router = APIRouter(
    prefix="/profiles",
    tags=["Profiles"],
    responses={404: {"description": "Not found"}},
)


@router.get("/me", response_model=ProfileOut)
async def get_my_profile(
    user_id: str = Depends(get_current_user_id),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    service = ProfileService(db)
    profile = await service.get_user_profile(user_id)

    if not profile:
        # Create default profile if it doesn't exist
        profile = await service.create_default_profile(user_id)

    return profile


@router.put("/me", response_model=ProfileOut)
async def update_my_profile(
    profile_data: ProfileUpdate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    service = ProfileService(db)
    profile = await service.update_profile(user_id, profile_data)

    if not profile:
        # Should create if not exists inside update, but just in case
        await service.create_default_profile(user_id)
        profile = await service.update_profile(user_id, profile_data)

    return profile
