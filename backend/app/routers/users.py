from fastapi import APIRouter
from backend.app.schemas.user import UserProfileResponse, UserProfileUpdate
from backend.app.db.repository import store

router = APIRouter(prefix="/users", tags=["User Profile"])

@router.get("/me", response_model=UserProfileResponse)
async def get_current_user_profile():
    """
    Returns the authenticated user's profile.
    """
    profile = store.get_user_profile(store.default_user_id)
    return UserProfileResponse(**profile)

@router.patch("/me", response_model=UserProfileResponse)
async def update_current_user_profile(payload: UserProfileUpdate):
    """
    Updates the authenticated user's profile (name, email, timezone, locale).
    """
    updated = store.update_user_profile(
        store.default_user_id,
        payload.model_dump(exclude_unset=True)
    )
    return UserProfileResponse(**updated)

