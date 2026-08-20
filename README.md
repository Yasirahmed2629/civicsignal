# CivicSignal

**A multilingual AI platform for aggregating citizen infrastructure requests and surfacing demand hotspots for policymakers.**

Built for the BRICS Digital Public Infrastructure challenge — CivicSignal lets citizens report local problems by text, voice, or SMS, in any language, and automatically turns scattered complaints into a prioritized, geolocated action list for governments.

## The Problem

Citizen feedback on infrastructure (broken roads, water outages, unsafe areas) is scattered across fragmented channels — SMS, WhatsApp, in-person complaints — with no way to see patterns, measure urgency, or align spending with real demand.

## What CivicSignal Does

1. **Ingests citizen requests** via text, voice, or SMS (multilingual, works offline)
2. **Understands each request** — detects language, classifies category (roads, water, electricity, sanitation, etc.), and scores urgency
3. **Geocodes** free-text locations into real coordinates
4. **Clusters nearby requests** into "demand hotspots" using spatial analysis
5. **Scores each hotspot** by priority — combining report volume, urgency, issue severity, and area-level demographic/infrastructure context
6. **Visualizes everything** on a live map dashboard for policymakers

## Architecture

```
Citizen (text / voice / SMS)
      ↓
FastAPI ingestion endpoints (/requests, /requests/voice, /requests/sms)
      ↓
NLU pipeline (language detection, category & urgency classification)
      ↓
Geocoding (free text → lat/lon)
      ↓
SQLite storage
      ↓
DBSCAN hotspot clustering + demographic-weighted priority scoring
      ↓
Live map dashboard (Leaflet.js)
```

## Tech Stack

- **Backend**: FastAPI + SQLAlchemy + SQLite
- **Speech-to-text**: faster-whisper (local, multilingual, offline-capable)
- **Language detection**: langdetect
- **Geocoding**: geopy + OpenStreetMap Nominatim
- **Clustering**: scikit-learn (DBSCAN with haversine distance)
- **Dashboard**: Leaflet.js (vanilla HTML/JS, no build step)

## Running Locally

```bash
# 1. Set up virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the server
uvicorn app.main:app --port 8080

# 4. Open the dashboard
# http://127.0.0.1:8080/dashboard

# 5. Explore the API
# http://127.0.0.1:8080/docs
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/requests` | Submit a citizen request via text |
| POST | `/requests/voice` | Submit a citizen request via voice recording |
| POST | `/requests/sms` | Submit a citizen request via SMS (Twilio-compatible webhook format) |
| GET | `/requests` | List all requests |
| GET | `/requests/{id}` | Get a single request |
| GET | `/hotspots` | Get detected demand hotspots, ranked by priority |
| GET | `/dashboard` | Live map visualization |

## Example: Submit a Request

```bash
curl -X POST http://127.0.0.1:8080/requests \
  -H "Content-Type: application/json" \
  -d '{
    "raw_text": "There is a broken water pipe leaking near the market",
    "channel": "web",
    "location_text": "Koramangala, Bengaluru"
  }'
```

Response — automatically enriched:
```json
{
  "id": "...",
  "raw_text": "There is a broken water pipe leaking near the market",
  "language": "en",
  "category": "water",
  "urgency": "high",
  "latitude": 12.9357,
  "longitude": 77.6134,
  ...
}
```

Multilingual, verified with Hindi:
```json
{
  "raw_text": "सड़क में बहुत बड़ा गड्ढा है, दुर्घटना हो सकती है",
  "language": "hi",
  "category": "roads",
  "urgency": "high"
}
```

Verified via SMS (Twilio-compatible form payload):
```bash
curl -X POST http://127.0.0.1:8080/requests/sms \
  -d "From=%2B919876543210&Body=Water%20supply%20has%20stopped&location_text=Koramangala"
```

## Priority Scoring

Each hotspot is scored 0-100 using a transparent, explainable formula that fuses citizen signal with area-level demographic and infrastructure context:

```
priority_score = (volume_score × 0.3)
                + (urgency_score × 0.3)
                + (category_score × 0.2)
                + (demographic_score × 0.2)
```

- **Volume**: number of citizen reports in the cluster (capped at 10)
- **Urgency**: highest urgency level reported (low/medium/high)
- **Category**: weighted by severity (safety/healthcare > water/electricity > roads/general)
- **Demographic/infrastructure**: population density + existing infrastructure weakness for the reported area — areas with more people affected or weaker existing infrastructure score higher, directly addressing the brief's requirement to combine citizen feedback with demographic and infrastructure-index data

## Roadmap (Post-Hackathon)

- [ ] Real SMS/WhatsApp provider integration (Twilio account — endpoint already built to spec)
- [ ] Expand demographic dataset beyond seeded demo areas
- [ ] Multi-country deployment configuration
- [ ] Authentication for policymaker-facing views
- [ ] Historical hotspot tracking over time

## Team / Submission

Built as a prototype for [Hackathon Name]. Demonstrates a working end-to-end pipeline from raw citizen input — across text, voice, and SMS, in multiple languages — to policymaker-ready, prioritized insight.