from fastapi import APIRouter
from uuid import UUID

from backend.app.db.repository import store
from backend.app.schemas.proposal import (
    ProposalResponse,
    ProposalItemResponse,
    ProposalApproveRequest,
    ProposalApproveResponse,
    ProposalItemPatch,
    ProposalClarificationRequest,
)
from backend.app.core.errors import ResourceNotFoundException

router = APIRouter(prefix="/proposals", tags=["Proposals & Approvals"])

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

