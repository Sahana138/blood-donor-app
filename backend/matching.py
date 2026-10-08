from datetime import date, timedelta
from math import radians, sin, cos, asin, sqrt
import models

# Recipient blood group -> donor groups that can give blood to them
CAN_RECEIVE_FROM = {
    "O-":  ["O-"],
    "O+":  ["O-", "O+"],
    "A-":  ["O-", "A-"],
    "A+":  ["O-", "O+", "A-", "A+"],
    "B-":  ["O-", "B-"],
    "B+":  ["O-", "O+", "B-", "B+"],
    "AB-": ["O-", "A-", "B-", "AB-"],
    "AB+": ["O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"],
}

MIN_GAP_DAYS = 90

def distance_km(lat1, lon1, lat2, lon2):
    """Straight-line distance between two map points (Haversine formula)."""
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    a = sin((lat2 - lat1) / 2) ** 2 + cos(lat1) * cos(lat2) * sin((lon2 - lon1) / 2) ** 2
    return 6371 * 2 * asin(sqrt(a))

def find_matches(db, blood_group, lat, lon, radius_km=10, limit=5, exclude_ids=()):
    cutoff = date.today() - timedelta(days=MIN_GAP_DAYS)
    donors = db.query(models.Donor).filter(
        models.Donor.blood_group.in_(CAN_RECEIVE_FROM[blood_group]),
        models.Donor.available == True,
    ).all()

    results = []
    for d in donors:
        if d.id in exclude_ids:
            continue
        if d.last_donated and d.last_donated > cutoff:
            continue  # donated too recently
        if d.latitude is None or d.longitude is None:
            continue
        dist = distance_km(lat, lon, d.latitude, d.longitude)
        if dist <= radius_km:
            results.append((d, round(dist, 1)))

    results.sort(key=lambda x: x[1])
    return results[:limit]