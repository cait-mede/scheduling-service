# Scheduling Service

## Overview

A Doodle-style meeting scheduling microservice built with FastAPI and SQLite. A creator proposes time slots, members mark which ones they can attend, and the creator confirms the best slot.

Scoped by `app_id` and `entity_id` so it can be reused across different applications and contexts.

## Data Model

Each **schedule**:
- `app_id` — identifies the calling application (e.g. `"book_club"`)
- `entity_id` — identifies what the schedule belongs to (e.g. a group ID)
- `slots` — list of proposed time slot strings
- `confirmed_slot` — index of the confirmed slot (null until confirmed)
- `created_by` — user ID of the creator

Each **availability** entry:
- One entry per user per schedule
- Stores which slot indices the user is available for
- Re-submitting overwrites the previous response (upsert)

## Setup

Install dependencies:
```bash
pip install -r requirements.txt
```

Start the server (runs on port 8002):
```bash
python -m uvicorn main:app --port 8002 --reload
```

---

## API

### POST /schedules — Create a schedule

**Body:**
```json
{
  "app_id": "book_club",
  "entity_id": "42",
  "slots": ["Friday June 6, 2025 at 7:00 PM", "Saturday June 7, 2025 at 2:00 PM"],
  "created_by": "user123"
}
```

**Response:**
```json
{ "schedule_id": 1 }
```

**Example:**
```bash
curl -X POST http://localhost:8002/schedules \
  -H "Content-Type: application/json" \
  -d '{
    "app_id": "book_club",
    "entity_id": "42",
    "slots": ["Friday June 6, 2025 at 7:00 PM", "Saturday June 7, 2025 at 2:00 PM"],
    "created_by": "user123"
  }'
```

---

### GET /schedules — List schedules for an entity

**Query params:** `app_id`, `entity_id`

**Response:** Array of schedules with slots, availability counts, and all responses.
```json
[
  {
    "schedule_id": 1,
    "app_id": "book_club",
    "entity_id": "42",
    "slots": [
      { "index": 0, "text": "Friday June 6, 2025 at 7:00 PM", "available_count": 3 },
      { "index": 1, "text": "Saturday June 7, 2025 at 2:00 PM", "available_count": 2 }
    ],
    "confirmed_slot": null,
    "created_by": "user123",
    "availability": {
      "user123": [0, 1],
      "user456": [0]
    }
  }
]
```

**Example:**
```bash
curl "http://localhost:8002/schedules?app_id=book_club&entity_id=42"
```

---

### POST /schedules/{schedule_id}/availability — Submit availability

**Body:**
```json
{ "user_id": "user456", "available_slots": [0, 1] }
```

Pass an empty list to indicate unavailable for all slots. Re-submitting overwrites the previous response.

**Response:**
```json
{ "status": "submitted" }
```

**Example:**
```bash
curl -X POST http://localhost:8002/schedules/1/availability \
  -H "Content-Type: application/json" \
  -d '{ "user_id": "user456", "available_slots": [0, 1] }'
```

---

### POST /schedules/{schedule_id}/confirm — Confirm a slot

**Body:**
```json
{ "slot_index": 0 }
```

**Response:**
```json
{ "status": "confirmed" }
```

Returns 400 if `slot_index` is out of range.

**Example:**
```bash
curl -X POST http://localhost:8002/schedules/1/confirm \
  -H "Content-Type: application/json" \
  -d '{ "slot_index": 0 }'
```
