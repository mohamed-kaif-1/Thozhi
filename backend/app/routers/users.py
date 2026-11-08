from fastapi import APIRouter, Depends
from backend.app.schemas.user import UserProfileResponse, UserProfileUpdate
from backend.app.db.repository import store
from backend.app.core.auth import get_current_user, AuthenticatedUser

router = APIRouter(prefix="/users", tags=["User Profile"])

@router.get("/me", response_model=UserProfileResponse)
async def get_current_user_profile(current_user: AuthenticatedUser = Depends(get_current_user)):
    """
    Returns the authenticated user's profile.
    """
    profile = store.get_user_profile(current_user.id, user_token=current_user.token)
    return UserProfileResponse(**profile)

@router.patch("/me", response_model=UserProfileResponse)
async def update_current_user_profile(
    payload: UserProfileUpdate,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Updates the authenticated user's profile (name, email, timezone, locale).
    """
    updated = store.update_user_profile(
        current_user.id,
        payload.model_dump(exclude_unset=True),
        user_token=current_user.token
    )
    return UserProfileResponse(**updated)
