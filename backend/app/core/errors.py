from fastapi import HTTPException, status
from typing import Optional, Dict, Any, Union, List

class AppException(HTTPException):
    def __init__(
        self,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail: str = "Internal server error occurred",
        error_code: str = "INTERNAL_ERROR",
        extra: Optional[Dict[str, Any]] = None
    ):
        super().__init__(status_code=status_code, detail=detail)
        self.error_code = error_code
        self.extra = extra or {}

    def to_problem_details(self) -> Dict[str, Any]:
        return {
            "type": f"https://thozhi.ai/errors/{self.error_code.lower()}",
            "title": self.error_code,
            "status": self.status_code,
            "detail": self.detail,
            "error_code": self.error_code,
            "invalid_params": self.extra
        }

class ASRProviderException(AppException):
    def __init__(self, detail: str = "Speech recognition service failed", provider: str = "UNKNOWN", status_code: int = status.HTTP_502_BAD_GATEWAY):
        super().__init__(
            status_code=status_code,
            detail=detail,
            error_code="ASR_FAILURE",
            extra={"provider": provider}
        )

class NLUProviderException(AppException):
    def __init__(
        self,
        detail: str = "Natural language understanding service failed",
        provider: str = "gemini",
        status_code: int = status.HTTP_502_BAD_GATEWAY,
        error_code: str = "NLU_FAILURE",
        extra: Optional[Dict[str, Any]] = None
    ):
        combined_extra = {"provider": provider}
        if extra:
            combined_extra.update(extra)
        super().__init__(
            status_code=status_code,
            detail=detail,
            error_code=error_code,
            extra=combined_extra
        )

class SchedulingCycleException(AppException):
    def __init__(self, cycle_info: Union[str, List[Any]]):
        detail = cycle_info if isinstance(cycle_info, str) else "Circular task dependency detected in schedule graph"
        extra = {"cycle": cycle_info} if isinstance(cycle_info, list) else {"details": cycle_info}
        super().__init__(
            status_code=getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422),
            detail=detail,
            error_code="CIRCULAR_DEPENDENCY",
            extra=extra
        )

class ProposalExpiredException(AppException):
    def __init__(self, proposal_id: str):
        super().__init__(
            status_code=status.HTTP_410_GONE,
            detail=f"Proposal {proposal_id} has expired and cannot be approved",
            error_code="PROPOSAL_EXPIRED"
        )

class IdempotencyConflictException(AppException):
    def __init__(self, key: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Concurrent or conflicting execution for idempotency key '{key}'",
            error_code="IDEMPOTENCY_CONFLICT"
        )

class ResourceNotFoundException(AppException):
    def __init__(self, detail: str = "Requested resource not found", resource_type: str = "resource", resource_id: Optional[str] = None):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            error_code="RESOURCE_NOT_FOUND",
            extra={"resource_type": resource_type, "resource_id": resource_id} if resource_id else {}
        )

class DuplicateTaskException(AppException):
    def __init__(self, title: str, scheduled_date: Optional[str] = None):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Active task with title '{title}' already exists for date {scheduled_date or 'today'}.",
            error_code="DUPLICATE_TASK",
            extra={"title": title, "scheduled_date": scheduled_date}
        )

class PermissionDeniedException(AppException):
    def __init__(self, detail: str = "Access denied for the requested resource"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code="PERMISSION_DENIED"
        )
