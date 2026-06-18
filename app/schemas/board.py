from __future__ import annotations
from typing import Optional, List
from pydantic import BaseModel
from schemas.user import UserResponse


class TicketResponse(BaseModel):
    """Ticket data used inside section detail responses."""
    id: int
    name: str
    description: Optional[str] = None
    section_id: int
    assigned_user_id: Optional[int] = None
    created_by_id: int

    model_config = {"from_attributes": True}


class SectionResponse(BaseModel):
    """Section data used inside board detail responses."""
    id: int
    name: str
    description: Optional[str] = None
    board_id: int
    tickets: List[TicketResponse] = []

    model_config = {"from_attributes": True}


class BoardMemberResponse(BaseModel):
    """Board member info with role."""
    id: int
    user_id: int
    role: str

    model_config = {"from_attributes": True}


class InvitationTokenResponse(BaseModel):
    """Invitation token returned to the board owner."""
    token: str

    model_config = {"from_attributes": True}


class BoardCreateRequest(BaseModel):
    """Request body for creating a new board."""
    name: str
    description: Optional[str] = None


class BoardResponse(BaseModel):
    """Basic board data returned in list responses."""
    id: int
    name: str
    description: Optional[str] = None
    owner_id: int

    model_config = {"from_attributes": True}


class BoardDetailResponse(BaseModel):
    """Full board detail including sections, members, and latest invitation token."""
    id: int
    name: str
    description: Optional[str] = None
    owner_id: int
    sections: List[SectionResponse] = []
    members: List[BoardMemberResponse] = []
    invitation_token: Optional[str] = None

    model_config = {"from_attributes": True}
