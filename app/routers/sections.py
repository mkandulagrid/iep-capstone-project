from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models.models import Board, BoardMember, Section, User
from schemas.section import SectionCreateRequest, SectionUpdateRequest, SectionResponse
from utils.dependencies import get_current_user

router = APIRouter(prefix="/sections", tags=["Sections"])


def _get_section_or_404(section_id: int, db: Session) -> Section:
    section = db.query(Section).filter(Section.id == section_id).first()
    if not section:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found.")
    return section


def _assert_board_member(board_id: int, user: User, db: Session) -> BoardMember:
    membership = (
        db.query(BoardMember)
        .filter(BoardMember.board_id == board_id, BoardMember.user_id == user.id)
        .first()
    )
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this board.",
        )
    return membership


def _assert_owner(board_id: int, user: User, db: Session) -> None:
    board = db.query(Board).filter(Board.id == board_id).first()
    if not board or board.owner_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the board owner can manage sections.",
        )


@router.post(
    "",
    response_model=SectionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a section on a board (owner only)",
)
def create_section(
    payload: SectionCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _assert_owner(payload.board_id, current_user, db)

    new_section = Section(
        name=payload.name,
        description=payload.description,
        board_id=payload.board_id,
    )
    db.add(new_section)
    db.commit()
    db.refresh(new_section)
    return new_section


@router.get(
    "/{section_id}",
    response_model=SectionResponse,
    summary="Get a section with its tickets",
)
def get_section(
    section_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    section = _get_section_or_404(section_id, db)
    _assert_board_member(section.board_id, current_user, db)
    return section


@router.put(
    "/{section_id}",
    response_model=SectionResponse,
    summary="Update a section (owner only)",
)
def update_section(
    section_id: int,
    payload: SectionUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    section = _get_section_or_404(section_id, db)
    _assert_owner(section.board_id, current_user, db)

    if payload.name is not None:
        section.name = payload.name
    if payload.description is not None:
        section.description = payload.description

    db.commit()
    db.refresh(section)
    return section


@router.delete(
    "/{section_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a section and all its tickets (owner only)",
)
def delete_section(
    section_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    section = _get_section_or_404(section_id, db)
    _assert_owner(section.board_id, current_user, db)

    db.delete(section)
    db.commit()
