"""
Database models for CivicSignal.

We start with ONE core table: citizen_requests.
Every request — whether it later comes in via SMS, WhatsApp, or voice —
lands here in the same normalized shape. This is the schema decision
that makes every later step (dedup, fusion, scoring) tractable.
"""

from sqlalchemy import Column, String, DateTime, Float, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import uuid

DATABASE_URL = "sqlite:///./civicsignal.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class CitizenRequest(Base):
    __tablename__ = "citizen_requests"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Raw input — always preserved, never overwritten
    raw_text = Column(String, nullable=False)
    language = Column(String, nullable=True)          # e.g. "hi", "en", "pt" — filled in later by langid step
    channel = Column(String, nullable=False)           # "web" | "sms" | "whatsapp" | "ivr"

    # Location — free text for now, geocoded to lat/lon in a later step
    location_text = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    # Filled in by later NLU steps — nullable now, populated by Step 3/4
    category = Column(String, nullable=True)           # e.g. "road", "water", "electricity"
    urgency = Column(String, nullable=True)             # e.g. "normal", "high"

    created_at = Column(DateTime, default=datetime.utcnow)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
