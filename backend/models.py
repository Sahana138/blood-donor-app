from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, Date, DateTime, ForeignKey
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    phone = Column(String(15))
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="donor")  # donor / requester / admin

class Donor(Base):
    __tablename__ = "donors"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    blood_group = Column(String(3), nullable=False)
    area = Column(String(100))
    latitude = Column(Float)
    longitude = Column(Float)
    last_donated = Column(Date, nullable=True)
    available = Column(Boolean, default=True)

class BloodRequest(Base):
    __tablename__ = "blood_requests"
    id = Column(Integer, primary_key=True, index=True)
    requester_id = Column(Integer, ForeignKey("users.id"))
    blood_group = Column(String(3), nullable=False)
    hospital = Column(String(150))
    latitude = Column(Float)
    longitude = Column(Float)
    urgency = Column(String(20), default="normal")
    status = Column(String(20), default="searching")  # searching / accepted / completed
    created_at = Column(DateTime, default=datetime.utcnow)

class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("blood_requests.id"))
    donor_id = Column(Integer, ForeignKey("donors.id"))
    wave = Column(Integer, default=1)
    status = Column(String(20), default="sent")  # sent / accepted / declined
    sent_at = Column(DateTime, default=datetime.utcnow)