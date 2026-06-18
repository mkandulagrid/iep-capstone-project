import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models.models import Board, BoardMember, InvitationToken, User
from schemas.board import (
    BoardCreateRequest,
    BoardDetailResponse,
    BoardResponse,
    InvitationTokenResponse,
    SectionResponse,
    BoardMemberResponse,
)
from utils.dependencies import get_current_user

router = APIRouter(prefix="/boards", tags=["Boards"])


def _get_board_or_404(board_id: int, db: Session) -> Board:
    board = db.query(Board).filter(Board.id == board_id).first()
    if not board:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Board not found.")
    return board


def _assert_board_access(board: Board, current_user: User, db: Session) -> BoardMember:
    membership = (
        db.query(BoardMember)
        .filter(BoardMember.board_id == board.id, BoardMember.user_id == current_user.id)
        .first()
    )
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this board.",
        )
    return membership


def _assert_owner(board: Board, current_user: User) -> None:
    if board.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the board owner can perform this action.",
        )


@router.post(
    "",
    response_model=BoardResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new board",
)
def create_board(
    payload: BoardCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    new_board = Board(
        name=payload.name,
        description=payload.description,
        owner_id=current_user.id,
    )
    db.add(new_board)
    db.flush()

    membership = BoardMember(board_id=new_board.id, user_id=current_user.id, role="owner")
    db.add(membership)
    db.commit()
    db.refresh(new_board)
    return new_board


@router.get(
    "",
    response_model=List[BoardResponse],
    summary="List all boards for the current user",
)
def list_boards(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    memberships = (
        db.query(BoardMember).filter(BoardMember.user_id == current_user.id).all()
    )
    board_ids = [m.board_id for m in memberships]
    boards = db.query(Board).filter(Board.id.in_(board_ids)).all()
    return boards


@router.get(
    "/{board_id}",
    response_model=BoardDetailResponse,
    summary="Get detailed info for a board",
)
def get_board_detail(
    board_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    board = _get_board_or_404(board_id, db)
    _assert_board_access(board, current_user, db)

    token_obj = (
        db.query(InvitationToken)
        .filter(InvitationToken.board_id == board_id, InvitationToken.is_used == False)
        .order_by(InvitationToken.id.desc())
        .first()
    )

    return BoardDetailResponse(
        id=board.id,
        name=board.name,
        description=board.description,
        owner_id=board.owner_id,
        sections=[
            SectionResponse(
                id=s.id,
                name=s.name,
                description=s.description,
                board_id=s.board_id,
                tickets=[
                    {
                        "id": t.id,
                        "name": t.name,
                        "description": t.description,
                        "section_id": t.section_id,
                        "assigned_user_id": t.assigned_user_id,
                        "created_by_id": t.created_by_id,
                    }
                    for t in s.tickets
                ],
            )
            for s in board.sections
        ],
        members=[
            BoardMemberResponse(id=m.id, user_id=m.user_id, role=m.role)
            for m in board.members
        ],
        invitation_token=token_obj.token if token_obj else None,
    )


@router.post(
    "/{board_id}/invite",
    response_model=InvitationTokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate an invitation token for a board (owner only)",
)
def generate_invitation(
    board_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    board = _get_board_or_404(board_id, db)
    _assert_owner(board, current_user)

    token_str = str(uuid.uuid4())
    invitation = InvitationToken(
        board_id=board_id,
        created_by_id=current_user.id,
        token=token_str,
        is_used=False,
    )
    db.add(invitation)
    db.commit()
    db.refresh(invitation)
    return InvitationTokenResponse(token=invitation.token)


@router.post(
    "/join/{token}",
    response_model=BoardResponse,
    summary="Join a board using an invitation token",
)
def join_board(
    token: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    invitation = (
        db.query(InvitationToken)
        .filter(InvitationToken.token == token, InvitationToken.is_used == False)
        .first()
    )
    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation token is invalid or has already been used.",
        )

    board = _get_board_or_404(invitation.board_id, db)

    existing_membership = (
        db.query(BoardMember)
        .filter(BoardMember.board_id == board.id, BoardMember.user_id == current_user.id)
        .first()
    )
    if not existing_membership:
        new_membership = BoardMember(
            board_id=board.id, user_id=current_user.id, role="member"
        )
        db.add(new_membership)

    invitation.is_used = True
    db.commit()
    db.refresh(board)
    return board
