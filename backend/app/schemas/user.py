from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID

class UserProfileResponse(BaseModel):
    id: UUID
    full_name: str
    email: str
    locale: str = "ta-IN"
    timezone: str = "Asia/Kolkata"

class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    locale: Optional[str] = None
    timezone: Optional[str] = None
