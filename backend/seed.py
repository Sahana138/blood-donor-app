import random
from datetime import date, timedelta
from database import SessionLocal, Base, engine
import models, auth

Base.metadata.create_all(bind=engine)
random.seed(42)
db = SessionLocal()

GROUPS = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
WEIGHTS = [30, 5, 30, 5, 8, 2, 15, 5]
pw = auth.hash_password("test1234")

for i in range(1, 31):
    email = f"seed{i}@example.com"
    if db.query(models.User).filter_by(email=email).first():
        continue
    user = models.User(name=f"Demo Donor {i}", email=email,
                       phone=f"90000000{i:02d}", password_hash=pw, role="donor")
    db.add(user)
    db.flush()
    last = None if random.random() < 0.3 else date.today() - timedelta(days=random.randint(10, 400))
    db.add(models.Donor(
        user_id=user.id,
        blood_group=random.choices(GROUPS, WEIGHTS)[0],
        area="Mysuru",
        latitude=12.2958 + random.uniform(-0.08, 0.08),
        longitude=76.6394 + random.uniform(-0.08, 0.08),
        last_donated=last,
        available=random.random() < 0.9,
    ))

db.commit()
db.close()
print("Seeded demo donors")