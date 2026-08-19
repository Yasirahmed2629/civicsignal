"""
CivicSignal API — Step 1: Citizen Request Ingestion

Run with:
    uvicorn app.main:app --reload

Then open http://127.0.0.1:8000/docs to see the interactive API docs
(FastAPI's Swagger UI) — this is a great first screenshot: it shows
the API is alive and you can submit/list requests right from the browser.
"""
from fastapi import FastAPI, Depends, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
import shutil
import uuid
import os

from app.services.stt import transcribe_audio
from app.services.nlu import analyze_request
from app.services.geocode import geocode_location
from app.services.hotspots import detect_hotspots
from app.models import init_db, get_db, CitizenRequest
from app.schemas import CitizenRequestCreate, CitizenRequestOut

app = FastAPI(
    title="CivicSignal API",
    description="Multilingual citizen feedback aggregation for infrastructure prioritization",
    version="0.1.0",
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/dashboard")
def dashboard():
    """Serve the live hotspot map dashboard."""
    return FileResponse("app/static/dashboard.html")


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/")
def root():
    return {"status": "ok", "service": "CivicSignal API", "step": "1 - ingestion"}


@app.post("/requests", response_model=CitizenRequestOut)
def create_request(payload: CitizenRequestCreate, db: Session = Depends(get_db)):
    """
    Submit a new citizen request.
    This is the single entry point every channel adapter (SMS, WhatsApp,
    voice transcript) will eventually call — for now we call it directly
    to prove the pipeline works end to end.
    """
    analysis = analyze_request(payload.raw_text)
    lat, lon = geocode_location(payload.location_text)
    request = CitizenRequest(
        raw_text=payload.raw_text,
        channel=payload.channel,
        location_text=payload.location_text,
        language=analysis["language"],
        category=analysis["category"],
        urgency=analysis["urgency"],
        latitude=lat,
        longitude=lon,
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    return request


@app.post("/requests/voice", response_model=CitizenRequestOut)
async def create_request_from_voice(
    audio: UploadFile = File(...),
    channel: str = "voice",
    location_text: str = "",
    db: Session = Depends(get_db),
):
    """
    Submit a citizen request via voice.
    Accepts an audio file, transcribes it using local Whisper,
    then reuses the exact same pipeline as the text endpoint.
    """
    temp_filename = f"temp_{uuid.uuid4().hex}_{audio.filename}"
    with open(temp_filename, "wb") as buffer:
        shutil.copyfileobj(audio.file, buffer)

    try:
        transcribed_text = transcribe_audio(temp_filename)
    finally:
        os.remove(temp_filename)

    analysis = analyze_request(transcribed_text)
    lat, lon = geocode_location(location_text)
    request = CitizenRequest(
        raw_text=transcribed_text,
        channel=channel,
        location_text=location_text,
        language=analysis["language"],
        category=analysis["category"],
        urgency=analysis["urgency"],
        latitude=lat,
        longitude=lon,
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    return request

@app.post("/requests/sms", response_model=CitizenRequestOut)
def create_request_from_sms(
    From: str = Form(...),
    Body: str = Form(...),
    location_text: str = Form(""),
    db: Session = Depends(get_db),
):
    """
    Submit a citizen request via SMS.
    Shaped to match real SMS provider webhook formats (e.g. Twilio),
    which POST form-encoded fields called 'From' (sender phone number)
    and 'Body' (message text) — not JSON. This means a real SMS provider
    could be pointed at this endpoint with no changes required.

    `location_text` is optional since raw SMS has no built-in location —
    in a real deployment this could come from a follow-up question to
    the citizen, a registered address on file, or a short-code region.
    If provided, it's geocoded the same way as the other channels.
    """
    analysis = analyze_request(Body)

    final_location_text = location_text if location_text.strip() else f"Reported via SMS from {From}"
    lat, lon = geocode_location(location_text) if location_text.strip() else (None, None)

    request = CitizenRequest(
        raw_text=Body,
        channel="sms",
        location_text=final_location_text,
        language=analysis["language"],
        category=analysis["category"],
        urgency=analysis["urgency"],
        latitude=lat,
        longitude=lon,
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    return request


@app.get("/requests", response_model=List[CitizenRequestOut])
def list_requests(db: Session = Depends(get_db)):
    """List all citizen requests received so far, newest first."""
    return db.query(CitizenRequest).order_by(CitizenRequest.created_at.desc()).all()


@app.get("/requests/{request_id}", response_model=CitizenRequestOut)
def get_request(request_id: str, db: Session = Depends(get_db)):
    """Fetch a single request by ID."""
    return db.query(CitizenRequest).filter(CitizenRequest.id == request_id).first()


@app.get("/hotspots")
def get_hotspots(db: Session = Depends(get_db)):
    """
    Detect demand hotspots by clustering nearby citizen requests.
    Groups geocoded requests within ~500m of each other; a hotspot
    requires at least 2 requests. Returns hotspots sorted by
    request count (most reports first).
    """
    all_requests = db.query(CitizenRequest).all()
    hotspots = detect_hotspots(all_requests)
    return {"hotspot_count": len(hotspots), "hotspots": hotspots}