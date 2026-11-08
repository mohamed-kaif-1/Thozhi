from fastapi import APIRouter, HTTPException, Query, status, Depends
from typing import List, Optional
from uuid import UUID

from backend.app.schemas.memory import (
    MemoryPreferenceCreate,
    MemoryPreferenceResponse,
    MemoryPreferencePatch,
    MemoryCategoryEnum,
    DurationPriorSuggestion,
    UserDataExportResponse,
    DataPurgeResponse,
)
from backend.app.db.repository import store
from backend.app.core.auth import get_current_user, AuthenticatedUser
from backend.app.core.errors import ResourceNotFoundException

router = APIRouter(prefix="/memory", tags=["Memory & Personalization"])

@router.get("/preferences", response_model=List[MemoryPreferenceResponse])
async def list_user_preferences(
    current_user: AuthenticatedUser = Depends(get_current_user),
    category: Optional[MemoryCategoryEnum] = Query(None),
    active_only: bool = Query(False)
):
    """
    Returns all stored user preferences and memory entries for the authenticated user.
    Users maintain total visibility and control over what the assistant remembers.
    """
    return store.list_memory_preferences(
        user_id=current_user.id,
        category=category,
        active_only=active_only,
        user_token=current_user.token
    )

@router.post("/preferences", response_model=MemoryPreferenceResponse)
async def set_preference(
    pref: MemoryPreferenceCreate,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Stores or updates a preference with explicit human consent for the authenticated user.
    Never silently records unapproved inferences.
    """
    return store.set_memory_preference(user_id=current_user.id, create_req=pref, user_token=current_user.token)

@router.get("/preferences/{pref_id}", response_model=MemoryPreferenceResponse)
async def get_preference(
    pref_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    return store.get_memory_preference(user_id=current_user.id, pref_id=pref_id, user_token=current_user.token)

@router.patch("/preferences/{pref_id}", response_model=MemoryPreferenceResponse)
async def patch_preference(
    pref_id: UUID,
    patch: MemoryPreferencePatch,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    return store.patch_memory_preference(user_id=current_user.id, pref_id=pref_id, patch=patch, user_token=current_user.token)

@router.delete("/preferences/{identifier}")
async def delete_preference(
    identifier: str,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Permanently revokes and purges a learned preference (Right to be Forgotten) for the authenticated user.
    Supports either UUID or preference_key identifier.
    """
    store.delete_memory_preference(user_id=current_user.id, identifier=identifier, user_token=current_user.token)
    return {"status": "purged", "preference_key": identifier, "message": "Preference permanently deleted."}

@router.post("/preferences/{pref_id}/toggle", response_model=MemoryPreferenceResponse)
async def toggle_preference(
    pref_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Temporarily disables or re-enables a memory preference without deletion for the authenticated user.
    """
    return store.toggle_memory_preference(user_id=current_user.id, pref_id=pref_id, user_token=current_user.token)

@router.get("/duration-priors/suggestions", response_model=List[DurationPriorSuggestion])
async def get_duration_prior_suggestions(current_user: AuthenticatedUser = Depends(get_current_user)):
    """
    Stage 6.3: Analyzes completed task history (actual vs estimated duration)
    to discover learned priors without hallucinating for the authenticated user.
    """
    return store.analyze_duration_priors(user_id=current_user.id, user_token=current_user.token)

@router.post("/export", response_model=UserDataExportResponse)
async def export_personal_data(current_user: AuthenticatedUser = Depends(get_current_user)):
    """
    Stage 6.4: Sovereign Data Portability.
    Exports all tasks, proposals, and memory preferences into structured JSON for the authenticated user.
    """
    return store.export_user_data(user_id=current_user.id, user_token=current_user.token)

@router.delete("/purge", response_model=DataPurgeResponse)
async def purge_all_personal_data(current_user: AuthenticatedUser = Depends(get_current_user)):
    """
    Stage 6.4: Sovereign Right to be Forgotten.
    Wipes all active and historical tenant tasks, proposals, and memory preferences for the authenticated user.
    """
    return store.purge_user_data(user_id=current_user.id, user_token=current_user.token)
