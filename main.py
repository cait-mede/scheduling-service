import json
from fastapi import FastAPI, HTTPException
from schemas import ScheduleCreate, Availability, ConfirmSlot
from db import init, get_db

app = FastAPI()
init()


def _build_schedule(schedule_id, app_id, entity_id, slots_json, confirmed_slot, created_by, book, db):
    slots = json.loads(slots_json)
    rows = db.execute(
        "SELECT user_id, available_slots FROM availability WHERE schedule_id=?",
        (schedule_id,)
    ).fetchall()

    counts = [0] * len(slots)
    all_availability = {}
    for user_id, avail_json in rows:
        indices = json.loads(avail_json)
        all_availability[user_id] = indices
        for i in indices:
            if 0 <= i < len(slots):
                counts[i] += 1

    return {
        "schedule_id": schedule_id,
        "app_id": app_id,
        "entity_id": entity_id,
        "slots": [{"index": i, "text": s, "available_count": counts[i]} for i, s in enumerate(slots)],
        "confirmed_slot": confirmed_slot,
        "created_by": created_by,
        "book": book,
        "availability": all_availability,
    }


@app.post("/schedules", status_code=201)
def create_schedule(schedule: ScheduleCreate):
    with get_db() as db:
        cur = db.execute(
            "INSERT INTO schedules (app_id, entity_id, slots, created_by, book) VALUES (?, ?, ?, ?, ?)",
            (schedule.app_id, schedule.entity_id, json.dumps(schedule.slots), schedule.created_by, schedule.book)
        )
        db.commit()
    return {"schedule_id": cur.lastrowid}


@app.get("/schedules")
def list_schedules(app_id: str, entity_id: str):
    with get_db() as db:
        rows = db.execute(
            "SELECT id, app_id, entity_id, slots, confirmed_slot, created_by, book FROM schedules WHERE app_id=? AND entity_id=?",
            (app_id, entity_id)
        ).fetchall()
        return [_build_schedule(*row, db) for row in rows]


@app.post("/schedules/{schedule_id}/availability")
def submit_availability(schedule_id: int, availability: Availability):
    with get_db() as db:
        schedule = db.execute("SELECT slots FROM schedules WHERE id=?", (schedule_id,)).fetchone()
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")

        num_slots = len(json.loads(schedule[0]))
        invalid = [i for i in availability.available_slots if i < 0 or i >= num_slots]
        if invalid:
            raise HTTPException(status_code=400, detail=f"Invalid slot indices: {invalid}")

        db.execute("""
        INSERT INTO availability (schedule_id, user_id, available_slots) VALUES (?, ?, ?)
        ON CONFLICT(schedule_id, user_id) DO UPDATE SET available_slots=excluded.available_slots
        """, (schedule_id, availability.user_id, json.dumps(availability.available_slots)))
        db.commit()

    return {"status": "submitted"}


@app.post("/schedules/{schedule_id}/confirm")
def confirm_slot(schedule_id: int, body: ConfirmSlot):
    with get_db() as db:
        schedule = db.execute("SELECT slots FROM schedules WHERE id=?", (schedule_id,)).fetchone()
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")
        if body.slot_index >= len(json.loads(schedule[0])):
            raise HTTPException(status_code=400, detail="Invalid slot index")

        db.execute("UPDATE schedules SET confirmed_slot=? WHERE id=?", (body.slot_index, schedule_id))
        db.commit()

    return {"status": "confirmed"}


@app.delete("/schedules/{schedule_id}")
def delete_schedule(schedule_id: int):
    with get_db() as db:
        if not db.execute("SELECT id FROM schedules WHERE id=?", (schedule_id,)).fetchone():
            raise HTTPException(status_code=404, detail="Schedule not found")
        db.execute("DELETE FROM availability WHERE schedule_id=?", (schedule_id,))
        db.execute("DELETE FROM schedules WHERE id=?", (schedule_id,))
        db.commit()
    return {"status": "deleted"}
