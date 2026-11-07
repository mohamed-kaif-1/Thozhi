from fastapi import APIRouter, HTTPException, Query, status
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
from backend.app.core.errors import ResourceNotFoundException

router = APIRouter(prefix="/memory", tags=["Memory & Personalization"])

@router.get("/preferences", response_model=List[MemoryPreferenceResponse])
async def list_user_preferences(
    category: Optional[MemoryCategoryEnum] = Query(None),
    active_only: bool = Query(False)
):
    """
    Returns all stored user preferences and memory entries.
    Users maintain total visibility and control over what the assistant remembers.
    """
    return store.list_memory_preferences(
        user_id=store.default_user_id,
        category=category,
        active_only=active_only
    )

@router.post("/preferences", response_model=MemoryPreferenceResponse)
async def set_preference(pref: MemoryPreferenceCreate):
    """
    Stores or updates a preference with explicit human consent.
    Never silently records unapproved inferences.
    """
    return store.set_memory_preference(user_id=store.default_user_id, create_req=pref)

@router.get("/preferences/{pref_id}", response_model=MemoryPreferenceResponse)
async def get_preference(pref_id: UUID):
    return store.get_memory_preference(user_id=store.default_user_id, pref_id=pref_id)

@router.patch("/preferences/{pref_id}", response_model=MemoryPreferenceResponse)
async def patch_preference(pref_id: UUID, patch: MemoryPreferencePatch):
    return store.patch_memory_preference(user_id=store.default_user_id, pref_id=pref_id, patch=patch)

@router.delete("/preferences/{identifier}")
async def delete_preference(identifier: str):
    """
    Permanently revokes and purges a learned preference (Right to be Forgotten).
    Supports either UUID or preference_key identifier.
    """
    store.delete_memory_preference(user_id=store.default_user_id, identifier=identifier)
    return {"status": "purged", "preference_key": identifier, "message": "Preference permanently deleted."}

@router.post("/preferences/{pref_id}/toggle", response_model=MemoryPreferenceResponse)
async def toggle_preference(pref_id: UUID):
    """
    Temporarily disables or re-enables a memory preference without deletion.
    """
    return store.toggle_memory_preference(user_id=store.default_user_id, pref_id=pref_id)

@router.get("/duration-priors/suggestions", response_model=List[DurationPriorSuggestion])
async def get_duration_prior_suggestions():
    """
    Stage 6.3: Analyzes completed task history (actual vs estimated duration)
    to discover learned priors without hallucinating.
    """
    return store.analyze_duration_priors(user_id=store.default_user_id)

@router.post("/export", response_model=UserDataExportResponse)
async def export_personal_data():
    """
    Stage 6.4: Sovereign Data Portability.
    Exports all tasks, proposals, and memory preferences into structured JSON.
    """
    return store.export_user_data(user_id=store.default_user_id)

@router.delete("/purge", response_model=DataPurgeResponse)
async def purge_all_personal_data():
    """
    Stage 6.4: Sovereign Right to be Forgotten.
    Wipes all active and historical tenant tasks, proposals, and memory preferences.
    """
    return store.purge_user_data(user_id=store.default_user_id)
