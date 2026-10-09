from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session
from database import get_db
import models, auth
from matching import CAN_RECEIVE_FROM
from alerts import send_wave, escalate

router = APIRouter(prefix="/requests", tags=["requests"])

class RequestCreate(BaseModel):
    blood_group: str
    hospital: str
    latitude: float
    longitude: float
    urgency: str = "normal"   # normal or urgent

    @field_validator("blood_group")
    @classmethod
    def check_group(cls, v):
        v = v.upper().strip()
        if v not in CAN_RECEIVE_FROM:
            raise ValueError("Invalid blood group")
        return v

    @field_validator("urgency")
    @classmethod
    def check_urgency(cls, v):
        if v not in ("normal", "urgent"):
            raise ValueError("Urgency must be normal or urgent")
        return v

class RequestOut(BaseModel):
    id: int
    blood_group: str
    hospital: str | None
    urgency: str
    status: str
    model_config = {"from_attributes": True}

class MatchOut(BaseModel):
    donor_id: int
    name: str
    blood_group: str
    area: str | None
    distance_km: float

class RequestResult(BaseModel):
    request: RequestOut
    alerted: list[MatchOut]

@router.post("", response_model=RequestResult, status_code=201)
def create_request(
    data: RequestCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: models.User = Depends(auth.get_current_user),
):
    if user.role != "requester":
        raise HTTPException(status_code=403, detail="Only requesters can create blood requests")

    req = models.BloodRequest(requester_id=user.id, **data.model_dump())
    db.add(req)
    db.commit()
    db.refresh(req)

    sent = send_wave(db, req, wave=1, radius_km=10)
    background_tasks.add_task(escalate, req.id)

    alerted = []
    for donor, dist in sent:
        donor_user = db.get(models.User, donor.user_id)
        alerted.append({
            "donor_id": donor.id,
            "name": donor_user.name,
            "blood_group": donor.blood_group,
            "area": donor.area,
            "distance_km": dist,
        })
    return {"request": req, "alerted": alerted}

@router.get("/{request_id}")
def request_status(
    request_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(auth.get_current_user),
):
    req = db.get(models.BloodRequest, request_id)
    if not req or req.requester_id != user.id:
        raise HTTPException(status_code=404, detail="Request not found")

    alert_rows = db.query(models.Alert).filter_by(request_id=req.id).all()

    accepted_donor = None
    nearby = []
    for a in alert_rows:
        donor = db.get(models.Donor, a.donor_id)
        if donor.latitude is not None and donor.longitude is not None:
            nearby.append({
                "lat": round(donor.latitude, 2),   # approximate on purpose
                "lng": round(donor.longitude, 2),
                "status": a.status,
            })
        if a.status == "accepted":
            donor_user = db.get(models.User, donor.user_id)
            accepted_donor = {
                "name": donor_user.name,
                "phone": donor_user.phone,
                "blood_group": donor.blood_group,
                "area": donor.area,
            }

    return {
        "id": req.id,
        "blood_group": req.blood_group,
        "hospital": req.hospital,
        "status": req.status,
        "latitude": req.latitude,
        "longitude": req.longitude,
        "donors_alerted": len(alert_rows),
        "nearby_donors": nearby,
        "accepted_donor": accepted_donor,
    }