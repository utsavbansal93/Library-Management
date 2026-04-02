"""Copy update and lending workflow endpoints."""

from typing import Optional
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models import Copy, Location
from schemas.artifacts import CopyDetail

router = APIRouter(tags=["copies"])


class CopyUpdate(BaseModel):
    location: Optional[str] = None
    condition: Optional[str] = None
    notes: Optional[str] = None
    internal_sku: Optional[str] = None


class LendRequest(BaseModel):
    borrower_name: str
    lent_date: Optional[str] = None  # ISO date string, defaults to today


class ReturnRequest(BaseModel):
    location: Optional[str] = None  # where to put it back, defaults to Large Shelf


@router.put("/copies/{copy_id}", response_model=CopyDetail)
def update_copy(
    copy_id: str, body: CopyUpdate, db: Session = Depends(get_db),
):
    copy = db.query(Copy).filter(Copy.copy_id == copy_id).first()
    if not copy:
        raise HTTPException(404, "Copy not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(copy, field, value)
    db.commit()
    db.refresh(copy)
    return copy


@router.put("/copies/{copy_id}/lend", response_model=CopyDetail)
def lend_copy(
    copy_id: str, body: LendRequest, db: Session = Depends(get_db),
):
    copy = db.query(Copy).filter(Copy.copy_id == copy_id).first()
    if not copy:
        raise HTTPException(404, "Copy not found")
    if copy.location == Location.LENT.value:
        raise HTTPException(
            409,
            f"Copy already lent to {copy.borrower_name}",
        )
    copy.location = Location.LENT.value
    copy.borrower_name = body.borrower_name
    copy.lent_date = (
        date.fromisoformat(body.lent_date) if body.lent_date
        else date.today()
    )
    db.commit()
    db.refresh(copy)
    return copy


@router.put("/copies/{copy_id}/return", response_model=CopyDetail)
def return_copy(
    copy_id: str, body: ReturnRequest, db: Session = Depends(get_db),
):
    copy = db.query(Copy).filter(Copy.copy_id == copy_id).first()
    if not copy:
        raise HTTPException(404, "Copy not found")
    if copy.location != Location.LENT.value:
        raise HTTPException(409, "Copy is not currently lent out")
    copy.location = body.location or Location.LARGE_SHELF.value
    copy.borrower_name = None
    copy.lent_date = None
    db.commit()
    db.refresh(copy)
    return copy
