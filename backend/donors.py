from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session
from database import get_db
import models, auth

router = APIRouter(prefix="/donors", tags=["donors"])

VALID_GROUPS = {"A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"}

class DonorProfile(BaseModel):
    blood_group: str
    area: str
    latitude: float
    longitude: float
    last_donated: date | None = None
    available: bool = True

    @field_validator("blood_group")
    @classmethod
    def check_group(cls, v):
        v = v.upper().strip()
        if v not in VALID_GROUPS:
            raise ValueError("Invalid blood group")
        return v

class DonorOut(DonorProfile):
    id: int
    model_config = {"from_attributes": True}

@router.put("/me", response_model=DonorOut)
def save_profile(
    data: DonorProfile,
    db: Session = Depends(get_db),
    user: models.User = Depends(auth.get_current_user),
):
    if user.role != "donor":
        raise HTTPException(status_code=403, detail="Only donors can create a donor profile")
    donor = db.query(models.Donor).filter(models.Donor.user_id == user.id).first()
    if donor is None:
        donor = models.Donor(user_id=user.id)
        db.add(donor)
    for field, value in data.model_dump().items():
        setattr(donor, field, value)
    db.commit()
    db.refresh(donor)
    return donor

@router.get("/me", response_model=DonorOut)
def get_profile(
    db: Session = Depends(get_db),
    user: models.User = Depends(auth.get_current_user),
):
    donor = db.query(models.Donor).filter(models.Donor.user_id == user.id).first()
    if donor is None:
        raise HTTPException(status_code=404, detail="Donor profile not created yet")
    return donor