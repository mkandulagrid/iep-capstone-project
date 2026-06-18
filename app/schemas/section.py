from typing import Optional, List
from pydantic import BaseModel


class TicketBriefResponse(BaseModel):
    """Minimal ticket info used inside section responses."""
    id: int
    name: str
    description: Optional[str] = None
    section_id: int
    assigned_user_id: Optional[int] = None
    created_by_id: int

    model_config = {"from_attributes": True}


class SectionCreateRequest(BaseModel):
    """Request body for creating a section on a board."""
    name: str
    description: Optional[str] = None
    board_id: int


class SectionUpdateRequest(BaseModel):
    """Request body for updating a section. board_id cannot be changed."""
    name: Optional[str] = None
    description: Optional[str] = None


class SectionResponse(BaseModel):
    """Full section response with its tickets."""
    id: int
    name: str
    description: Optional[str] = None
    board_id: int
    tickets: List[TicketBriefResponse] = []

    model_config = {"from_attributes": True}
