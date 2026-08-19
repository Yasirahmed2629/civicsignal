# CivicSignal — Step 1: Citizen Request Ingestion API

## What this step does
A working FastAPI backend that accepts a citizen's infrastructure request
(text + optional location) and stores it in a database. This is the
foundation every later step builds on — voice transcription, translation,
classification, and prioritization will all feed into this same table.

## Setup

```bash
# 1. Create a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate        # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the server
uvicorn app.main:app --reload
```

## Test it

Open your browser to:

**http://127.0.0.1:8000/docs**

This is FastAPI's auto-generated interactive docs (Swagger UI). You'll see:
- `POST /requests` — submit a new citizen request
- `GET /requests` — list all requests
- `GET /requests/{id}` — fetch one request

### Try it from the docs UI:
1. Click on `POST /requests` → "Try it out"
2. Paste this into the request body:
   ```json
   {
     "raw_text": "The main road near the market has a huge pothole causing accidents",
     "channel": "web",
     "location_text": "Ward 4, near Central Market"
   }
   ```
3. Click "Execute" — you should get a `200` response with the saved request, including a generated `id` and `created_at` timestamp.
4. Then try `GET /requests` → "Try it out" → "Execute" to see it listed.

### Or test from the command line:
```bash
curl -X POST http://127.0.0.1:8000/requests \
  -H "Content-Type: application/json" \
  -d '{"raw_text": "Water supply has been cut for 5 days", "channel": "web", "location_text": "Sector 12"}'

curl http://127.0.0.1:8000/requests
```

## What to screenshot
Either:
- The Swagger UI at `/docs` showing a successful `POST /requests` response, **or**
- The terminal output of the `curl` commands above showing the saved request and the list.

## Project structure so far
```
civicsignal/
├── app/
│   ├── __init__.py
│   ├── models.py      # DB schema — the CitizenRequest table
│   ├── schemas.py      # API input/output validation
│   └── main.py         # FastAPI app + endpoints
├── requirements.txt
└── README.md
```

## What's next (Step 2 preview)
Once this is running and you've submitted a couple of test requests, Step 2
will add **voice input**: upload an audio file, transcribe it with Whisper,
and feed the transcript into this same `/requests` pipeline — so a citizen
can report an issue by speaking instead of typing.
