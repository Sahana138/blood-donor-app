import os
import html
import asyncio
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from jose import jwt, JWTError
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db, SessionLocal
import models, auth
from matching import find_matches, distance_km
from email_service import send_email

router = APIRouter(prefix="/alerts", tags=["alerts"])

BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000")
WAVE_MINUTES = float(os.getenv("WAVE_MINUTES", "10"))


def make_token(alert_id: int) -> str:
    payload = {"alert_id": alert_id, "exp": datetime.utcnow() + timedelta(hours=24)}
    return jwt.encode(payload, auth.SECRET_KEY, algorithm=auth.ALGORITHM)


def try_accept(db, alert, req):
    """Only the first donor can win a request. Returns True if this donor won."""
    won = (
        db.query(models.BloodRequest)
        .filter(models.BloodRequest.id == req.id, models.BloodRequest.status == "searching")
        .update({"status": "accepted"}, synchronize_session=False)
    )
    if won == 1:
        alert.status = "accepted"
    db.commit()
    return won == 1


def send_wave(db, req, wave, radius_km):
    """Email the next 5 nearest eligible donors who were not alerted yet."""
    already = [a.donor_id for a in db.query(models.Alert)
               .filter(models.Alert.request_id == req.id).all()]
    found = find_matches(db, req.blood_group, req.latitude, req.longitude,
                         radius_km=radius_km, limit=5, exclude_ids=already)
    sent = []
    for donor, dist in found:
        alert = models.Alert(request_id=req.id, donor_id=donor.id, wave=wave, status="sent")
        db.add(alert)
        db.commit()
        db.refresh(alert)

        user = db.get(models.User, donor.user_id)
        link = f"{BASE_URL}/alerts/respond?token={make_token(alert.id)}"
        label = "URGENT: " if req.urgency == "urgent" else ""
        subject = f"{label}{req.blood_group} blood needed near you"
        body = (
            f"Hello {user.name},\n\n"
            f"{req.blood_group} blood is needed at {req.hospital}, "
            f"about {dist} km from you.\n\n"
            f"Can you donate?\n"
            f"Accept:  {link}&action=accept\n"
            f"Decline: {link}&action=decline\n\n"
            f"If you cannot donate, you can ignore this email."
        )
        try:
            send_email(user.email, subject, body)
        except Exception as e:
            print(f"Email failed for {user.email}: {e}")
        sent.append((donor, dist))
    return sent


def _next_wave(request_id, wave, radius_km) -> bool:
    db = SessionLocal()
    try:
        req = db.get(models.BloodRequest, request_id)
        if not req or req.status != "searching":
            return False
        sent = send_wave(db, req, wave, radius_km)
        print(f"[wave {wave}] alerted {len(sent)} more donors for request {request_id}")
        return True
    finally:
        db.close()


async def escalate(request_id: int):
    """Runs in the background: if nobody accepts, alert more donors."""
    for wave, radius in [(2, 20), (3, 30)]:
        await asyncio.sleep(WAVE_MINUTES * 60)
        still_open = await asyncio.to_thread(_next_wave, request_id, wave, radius)
        if not still_open:
            break


def page(title, message):
    return HTMLResponse(
        "<html><body style='font-family:sans-serif;text-align:center;margin-top:60px'>"
        f"<h2>{html.escape(title)}</h2><p>{html.escape(message)}</p></body></html>"
    )


# ---------- Email link (Accept / Decline) ----------
@router.get("/respond", response_class=HTMLResponse)
def respond(token: str, action: str, db: Session = Depends(get_db)):
    try:
        data = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
        alert = db.get(models.Alert, data["alert_id"])
    except (JWTError, KeyError):
        alert = None
    if alert is None:
        return page("Link not valid", "This link is invalid or has expired.")

    req = db.get(models.BloodRequest, alert.request_id)

    if action == "decline":
        alert.status = "declined"
        db.commit()
        return page("Thank you", "We have noted that you cannot donate this time.")

    if action != "accept":
        return page("Unknown action", "Please use the links from the email.")

    if alert.status == "accepted":
        return page("Already accepted", "You have already accepted this request.")
    if not try_accept(db, alert, req):
        return page("Already filled", "Another donor has already accepted. Thank you for being ready to help!")
    return page("Thank you!", f"You accepted the request at {req.hospital}. The requester can now contact you.")


# ---------- In-app donor inbox ----------
class RespondBody(BaseModel):
    action: str  # accept or decline


@router.get("/mine")
def my_alerts(
    db: Session = Depends(get_db),
    user: models.User = Depends(auth.get_current_user),
):
    donor = db.query(models.Donor).filter_by(user_id=user.id).first()
    if not donor:
        return []
    rows = (
        db.query(models.Alert, models.BloodRequest)
        .join(models.BloodRequest, models.Alert.request_id == models.BloodRequest.id)
        .filter(models.Alert.donor_id == donor.id)
        .order_by(models.Alert.sent_at.desc())
        .limit(10)
        .all()
    )
    out = []
    for alert, req in rows:
        dist = None
        if None not in (donor.latitude, donor.longitude, req.latitude, req.longitude):
            dist = round(distance_km(donor.latitude, donor.longitude, req.latitude, req.longitude), 1)
        out.append({
            "alert_id": alert.id,
            "blood_group": req.blood_group,
            "hospital": req.hospital,
            "urgency": req.urgency,
            "distance_km": dist,
            "my_status": alert.status,
            "request_status": req.status,
        })
    return out


@router.post("/{alert_id}/respond")
def respond_in_app(
    alert_id: int,
    body: RespondBody,
    db: Session = Depends(get_db),
    user: models.User = Depends(auth.get_current_user),
):
    donor = db.query(models.Donor).filter_by(user_id=user.id).first()
    alert = db.get(models.Alert, alert_id)
    if not donor or not alert or alert.donor_id != donor.id:
        raise HTTPException(status_code=404, detail="Alert not found")
    req = db.get(models.BloodRequest, alert.request_id)

    if body.action == "decline":
        alert.status = "declined"
        db.commit()
        return {"result": "declined", "message": "Thank you. We have noted that you cannot donate this time."}

    if body.action != "accept":
        raise HTTPException(status_code=400, detail="Action must be accept or decline")

    if alert.status == "accepted":
        return {"result": "already_accepted", "message": "You have already accepted this request."}
    if not try_accept(db, alert, req):
        return {"result": "filled", "message": "Another donor has already accepted. Thank you for being ready to help!"}
    return {"result": "accepted", "message": f"Thank you for accepting! The requester at {req.hospital} can now contact you."}