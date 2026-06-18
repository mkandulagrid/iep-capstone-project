from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models.models import Board, BoardMember, Section, Ticket, User
from schemas.ticket import TicketCreateRequest, TicketUpdateRequest, TicketResponse
from utils.dependencies import get_current_user

router = APIRouter(prefix="/tickets", tags=["Tickets"])


def _get_ticket_or_404(ticket_id: int, db: Session) -> Ticket:
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found.")
    return ticket


def _get_section_or_404(section_id: int, db: Session) -> Section:
    section = db.query(Section).filter(Section.id == section_id).first()
    if not section:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found.")
    return section


def _get_membership(board_id: int, user: User, db: Session) -> BoardMember | None:
    return (
        db.query(BoardMember)
        .filter(BoardMember.board_id == board_id, BoardMember.user_id == user.id)
        .first()
    )


def _assert_board_member(board_id: int, user: User, db: Session) -> BoardMember:
    membership = _get_membership(board_id, user, db)
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this board.",
        )
    return membership


def _get_board_owner_id(board_id: int, db: Session) -> int:
    board = db.query(Board).filter(Board.id == board_id).first()
    if not board:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Board not found.")
    return board.owner_id


@router.post(
    "",
    response_model=TicketResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a ticket in a section",
)
def create_ticket(
    payload: TicketCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    section = _get_section_or_404(payload.section_id, db)
    _assert_board_member(section.board_id, current_user, db)

    if payload.assigned_user_id:
        assigned_membership = (
            db.query(BoardMember)
            .filter(
                BoardMember.board_id == section.board_id,
                BoardMember.user_id == payload.assigned_user_id,
            )
            .first()
        )
        if not assigned_membership:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The assigned user is not a member of this board.",
            )

    new_ticket = Ticket(
        name=payload.name,
        description=payload.description,
        section_id=payload.section_id,
        assigned_user_id=payload.assigned_user_id,
        created_by_id=current_user.id,
    )
    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)
    return new_ticket


@router.get(
    "/{ticket_id}",
    response_model=TicketResponse,
    summary="Get a ticket by ID",
)
def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ticket = _get_ticket_or_404(ticket_id, db)
    section = _get_section_or_404(ticket.section_id, db)
    _assert_board_member(section.board_id, current_user, db)
    return ticket


@router.put(
    "/{ticket_id}",
    response_model=TicketResponse,
    summary="Update a ticket",
)
def update_ticket(
    ticket_id: int,
    payload: TicketUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ticket = _get_ticket_or_404(ticket_id, db)
    section = _get_section_or_404(ticket.section_id, db)
    board_id = section.board_id
    _assert_board_member(board_id, current_user, db)

    owner_id = _get_board_owner_id(board_id, db)
    is_owner = current_user.id == owner_id
    if not is_owner and ticket.created_by_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only edit tickets that you created.",
        )

    if payload.section_id is not None and payload.section_id != ticket.section_id:
        new_section = _get_section_or_404(payload.section_id, db)
        if new_section.board_id != board_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot move a ticket to a section on a different board.",
            )
        ticket.section_id = payload.section_id

    if payload.name is not None:
        ticket.name = payload.name
    if payload.description is not None:
        ticket.description = payload.description
    if payload.assigned_user_id is not None:
        ticket.assigned_user_id = payload.assigned_user_id

    db.commit()
    db.refresh(ticket)
    return ticket


@router.delete(
    "/{ticket_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a ticket",
)
def delete_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ticket = _get_ticket_or_404(ticket_id, db)
    section = _get_section_or_404(ticket.section_id, db)
    board_id = section.board_id
    _assert_board_member(board_id, current_user, db)

    owner_id = _get_board_owner_id(board_id, db)
    is_owner = current_user.id == owner_id
    if not is_owner and ticket.created_by_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete tickets that you created.",
        )

    db.delete(ticket)
    db.commit()
