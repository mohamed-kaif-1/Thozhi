from fastapi import APIRouter, Query
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
from backend.app.core.errors import ResourceNotFoundException

router = APIRouter(prefix="/proposals", tags=["Proposals & Approvals"])

@router.get("", response_model=List[ProposalResponse])
async def list_proposals(
    status: Optional[str] = Query(None, description="Filter by status (e.g. 'PENDING_REVIEW', 'APPROVED', 'COMMITTED', 'REJECTED')"),
    capture_id: Optional[UUID] = Query(None, description="Filter by source capture ID"),
    user_id: Optional[UUID] = None
):
    """
    Lists proposals in the approval queue.
    Supports filtering by status and source capture ID.
    """
    return store.list_proposals(user_id=user_id, status=status, capture_id=capture_id)

@router.post("/batch/approve", response_model=ProposalBatchActionResponse)
async def batch_approve(request: ProposalBatchApproveRequest):
    """
    Batch approves multiple proposals from the pending queue and commits their tasks.
    """
    res = store.batch_approve_proposals(
        proposal_ids=request.proposal_ids,
        user_id=store.default_user_id,
        idempotency_key=request.idempotency_key
    )
    return ProposalBatchActionResponse(
        affected_count=res["affected_count"],
        proposal_ids=res["proposal_ids"],
        message=res["message"]
    )

@router.post("/batch/reject", response_model=ProposalBatchActionResponse)
async def batch_reject(request: ProposalBatchRejectRequest):
    """
    Batch rejects multiple proposals from the pending queue.
    """
    res = store.batch_reject_proposals(
        proposal_ids=request.proposal_ids,
        user_id=store.default_user_id,
        reason=request.reason
    )
    return ProposalBatchActionResponse(
        affected_count=res["affected_count"],
        proposal_ids=res["proposal_ids"],
        message=res["message"]
    )

@router.get("/{proposal_id}", response_model=ProposalResponse)
async def get_proposal(proposal_id: UUID):
    prop = store.get_proposal(proposal_id)
    if not prop:
        raise ResourceNotFoundException(
            detail=f"Proposal with ID {proposal_id} does not exist.",
            resource_type="proposal",
            resource_id=str(proposal_id)
        )
    return prop

@router.post("/{proposal_id}/reject", response_model=ProposalResponse)
async def reject_proposal(
    proposal_id: UUID,
    request: Optional[ProposalRejectRequest] = None
):
    """
    Explicitly marks proposal as REJECTED without generating scheduled tasks.
    """
    reason = request.reason if request else "User rejected proposal"
    try:
        return store.reject_proposal(proposal_id=proposal_id, reason=reason)
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
    request: Optional[ProposalTranslateRequest] = None
):
    """
    Translates proposal transcript, intent summary, item titles, descriptions,
    and clarification questions to target_language ('en', 'ta', or 'original').
    Supports both query parameter and JSON body for frontend convenience.
    """
    target = target_language or (request.target_language if request else "en")
    return await store.translate_proposal(proposal_id=proposal_id, target_language=target)

@router.patch("/{proposal_id}/items/{item_id}", response_model=ProposalItemResponse)
async def patch_proposal_item(proposal_id: UUID, item_id: UUID, patch: ProposalItemPatch):
    """
    Allows human editing of an extracted item (title, duration, priority, deadline)
    before final commitment.
    """
    return store.update_proposal_item(proposal_id=proposal_id, item_id=item_id, patch=patch)

@router.post("/{proposal_id}/clarify", response_model=ProposalResponse)
async def clarify_proposal(proposal_id: UUID, request: ProposalClarificationRequest):
    """
    Clarification feedback loop:
    User answers targeted questions to disambiguate deadlines, durations, or commitment levels.
    """
    return store.apply_clarifications(proposal_id=proposal_id, request=request)

@router.post("/{proposal_id}/approve", response_model=ProposalApproveResponse)
async def approve_proposal(proposal_id: UUID, request: ProposalApproveRequest):
    """
    Core principle gate:
    User commits approval/rejection decisions.
    Only approved items are converted to tasks in the database.
    """
    try:
        return store.approve_proposal(
            proposal_id=proposal_id,
            user_id=store.default_user_id,
            request=request
        )
    except KeyError:
        raise ResourceNotFoundException(
            detail=f"Proposal with ID {proposal_id} does not exist for approval.",
            resource_type="proposal",
            resource_id=str(proposal_id)
        )

