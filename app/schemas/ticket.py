from typing import Optional
from pydantic import BaseModel


class TicketCreateRequest(BaseModel):
    """Request body for creating a new ticket."""
    name: str
    description: Optional[str] = None
    section_id: int
    assigned_user_id: Optional[int] = None


class TicketUpdateRequest(BaseModel):
    """Request body for updating a ticket. section_id can change but must stay on same board."""
    name: Optional[str] = None
    description: Optional[str] = None
    section_id: Optional[int] = None
    assigned_user_id: Optional[int] = None


class TicketResponse(BaseModel):
    """Full ticket response."""
    id: int
    name: str
    description: Optional[str] = None
    section_id: int
    assigned_user_id: Optional[int] = None
    created_by_id: int

    model_config = {"from_attributes": True}
