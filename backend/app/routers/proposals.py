from fastapi import APIRouter, Query, Depends
from typing import Optional, List
from uuid import UUID

from backend.app.db.repository import store
from backend.app.schemas.proposal import (
    ProposalResponse,
    ProposalItemResponse,
    ProposalApproveRequest,
    ProposalApproveResponse,
    ProposalItemPatch,
    ProposalClarificationRequest,
    ProposalTranslateRequest,
    ProposalRejectRequest,
    ProposalBatchApproveRequest,
    ProposalBatchRejectRequest,
    ProposalBatchActionResponse,
)
from backend.app.core.auth import get_current_user, AuthenticatedUser
from backend.app.core.errors import ResourceNotFoundException

router = APIRouter(prefix="/proposals", tags=["Proposals & Approvals"])

@router.get("", response_model=List[ProposalResponse])
async def list_proposals(
    current_user: AuthenticatedUser = Depends(get_current_user),
    status: Optional[str] = Query(None, description="Filter by status (e.g. 'PENDING_REVIEW', 'APPROVED', 'COMMITTED', 'REJECTED')"),
    capture_id: Optional[UUID] = Query(None, description="Filter by source capture ID")
):
    """
    Lists proposals in the approval queue scoped strictly to the authenticated user.
    Supports filtering by status and source capture ID.
    """
    return store.list_proposals(user_id=current_user.id, status=status, capture_id=capture_id, user_token=current_user.token)

@router.post("/batch/approve", response_model=ProposalBatchActionResponse)
async def batch_approve(
    request: ProposalBatchApproveRequest,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Batch approves multiple proposals from the pending queue and commits their tasks for the authenticated user.
    """
    res = store.batch_approve_proposals(
        proposal_ids=request.proposal_ids,
        user_id=current_user.id,
        idempotency_key=request.idempotency_key,
        user_token=current_user.token
    )
    return ProposalBatchActionResponse(
        affected_count=res["affected_count"],
        proposal_ids=res["proposal_ids"],
        message=res["message"]
    )

@router.post("/batch/reject", response_model=ProposalBatchActionResponse)
async def batch_reject(
    request: ProposalBatchRejectRequest,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Batch rejects multiple proposals from the pending queue for the authenticated user.
    """
    res = store.batch_reject_proposals(
        proposal_ids=request.proposal_ids,
        user_id=current_user.id,
        reason=request.reason,
        user_token=current_user.token
    )
    return ProposalBatchActionResponse(
        affected_count=res["affected_count"],
        proposal_ids=res["proposal_ids"],
        message=res["message"]
    )

@router.get("/{proposal_id}", response_model=ProposalResponse)
async def get_proposal(
    proposal_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    prop = store.get_proposal(proposal_id, user_id=current_user.id, user_token=current_user.token)
    if not prop or (hasattr(prop, "user_id") and prop.user_id != current_user.id):
        raise ResourceNotFoundException(
            detail=f"Proposal with ID {proposal_id} does not exist.",
            resource_type="proposal",
            resource_id=str(proposal_id)
        )
    return prop

@router.post("/{proposal_id}/reject", response_model=ProposalResponse)
async def reject_proposal(
    proposal_id: UUID,
    request: Optional[ProposalRejectRequest] = None,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Explicitly marks proposal as REJECTED without generating scheduled tasks.
    Enforces tenant ownership.
    """
    prop = store.get_proposal(proposal_id, user_id=current_user.id, user_token=current_user.token)
    if not prop or (hasattr(prop, "user_id") and prop.user_id != current_user.id):
        raise ResourceNotFoundException(
            detail=f"Proposal with ID {proposal_id} does not exist.",
            resource_type="proposal",
            resource_id=str(proposal_id)
        )

    reason = request.reason if request else "User rejected proposal"
    try:
        return store.reject_proposal(proposal_id=proposal_id, user_id=current_user.id, reason=reason, user_token=current_user.token)
    except KeyError:
        raise ResourceNotFoundException(
            detail=f"Proposal with ID {proposal_id} does not exist.",
            resource_type="proposal",
            resource_id=str(proposal_id)
        )

@router.post("/{proposal_id}/translate", response_model=ProposalResponse)
async def translate_proposal(
    proposal_id: UUID,
    target_language: Optional[str] = Query(None, description="Target language ('en', 'ta', 'original')"),
    request: Optional[ProposalTranslateRequest] = None,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Translates proposal transcript, intent summary, item titles, descriptions,
    and clarification questions to target_language ('en', 'ta', or 'original').
    Supports both query parameter and JSON body for frontend convenience.
    Enforces tenant ownership.
    """
    prop = store.get_proposal(proposal_id, user_id=current_user.id, user_token=current_user.token)
    if not prop or (hasattr(prop, "user_id") and prop.user_id != current_user.id):
        raise ResourceNotFoundException(
            detail=f"Proposal with ID {proposal_id} does not exist.",
            resource_type="proposal",
            resource_id=str(proposal_id)
        )

    target = target_language or (request.target_language if request else "en")
    return await store.translate_proposal(proposal_id=proposal_id, target_language=target, user_id=current_user.id, user_token=current_user.token)

@router.patch("/{proposal_id}/items/{item_id}", response_model=ProposalItemResponse)
async def patch_proposal_item(
    proposal_id: UUID,
    item_id: UUID,
    patch: ProposalItemPatch,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Allows human editing of an extracted item (title, duration, priority, deadline)
    before final commitment.
    Enforces tenant ownership.
    """
    prop = store.get_proposal(proposal_id, user_id=current_user.id, user_token=current_user.token)
    if not prop or (hasattr(prop, "user_id") and prop.user_id != current_user.id):
        raise ResourceNotFoundException(
            detail=f"Proposal with ID {proposal_id} does not exist.",
            resource_type="proposal",
            resource_id=str(proposal_id)
        )
    return store.update_proposal_item(proposal_id=proposal_id, item_id=item_id, patch=patch, user_id=current_user.id, user_token=current_user.token)

@router.post("/{proposal_id}/clarify", response_model=ProposalResponse)
async def clarify_proposal(
    proposal_id: UUID,
    request: ProposalClarificationRequest,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Clarification feedback loop:
    User answers targeted questions to disambiguate deadlines, durations, or commitment levels.
    Enforces tenant ownership.
    """
    prop = store.get_proposal(proposal_id, user_id=current_user.id, user_token=current_user.token)
    if not prop or (hasattr(prop, "user_id") and prop.user_id != current_user.id):
        raise ResourceNotFoundException(
            detail=f"Proposal with ID {proposal_id} does not exist.",
            resource_type="proposal",
            resource_id=str(proposal_id)
        )
    return store.apply_clarifications(proposal_id=proposal_id, request=request, user_id=current_user.id, user_token=current_user.token)

@router.post("/{proposal_id}/approve", response_model=ProposalApproveResponse)
async def approve_proposal(
    proposal_id: UUID,
    request: ProposalApproveRequest,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Core principle gate:
    User commits approval/rejection decisions.
    Only approved items are converted to tasks in the database under the authenticated user.
    """
    prop = store.get_proposal(proposal_id, user_id=current_user.id, user_token=current_user.token)
    if not prop or (hasattr(prop, "user_id") and prop.user_id != current_user.id):
        raise ResourceNotFoundException(
            detail=f"Proposal with ID {proposal_id} does not exist for approval.",
            resource_type="proposal",
            resource_id=str(proposal_id)
        )

    try:
        return store.approve_proposal(
            proposal_id=proposal_id,
            user_id=current_user.id,
            request=request,
            user_token=current_user.token
        )
    except KeyError:
        raise ResourceNotFoundException(
            detail=f"Proposal with ID {proposal_id} does not exist for approval.",
            resource_type="proposal",
            resource_id=str(proposal_id)
        )
