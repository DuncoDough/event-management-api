import os
import io
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import motor.motor_asyncio
from bson import ObjectId

# Load environment variables
load_dotenv()

app = FastAPI(title="Event Management API")

# MongoDB connection
MONGO_URI = os.getenv("MONGO_URI")
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
db = client.event_management_db

# -------------------- MODELS --------------------

class Event(BaseModel):
    name: str
    description: str
    date: str
    venue_id: str
    max_attendees: int = Field(gt=0)

class Attendee(BaseModel):
    name: str
    email: str
    phone: Optional[str]

class Venue(BaseModel):
    name: str
    address: str
    capacity: int = Field(gt=0)

class Booking(BaseModel):
    event_id: str
    attendee_id: str
    ticket_type: str
    quantity: int = Field(gt=0)

# -------------------- HELPERS --------------------

async def get_file_or_404(collection, file_id: str):
    try:
        oid = ObjectId(file_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid file id")

    doc = await collection.find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="File not found")
    return doc

# -------------------- ROUTES --------------------

@app.get("/")
def root():
    return {"status": "API running"}

# EVENTS
@app.post("/events")
async def create_event(event: Event):
    result = await db.events.insert_one(event.dict())
    return {"id": str(result.inserted_id)}

@app.get("/events")
async def get_events():
    events = await db.events.find().to_list(100)
    for e in events:
        e["_id"] = str(e["_id"])
    return events

# ATTENDEES
@app.post("/attendees")
async def create_attendee(attendee: Attendee):
    result = await db.attendees.insert_one(attendee.dict())
    return {"id": str(result.inserted_id)}

@app.get("/attendees")
async def get_attendees():
    attendees = await db.attendees.find().to_list(100)
    for a in attendees:
        a["_id"] = str(a["_id"])
    return attendees

# VENUES
@app.post("/venues")
async def create_venue(venue: Venue):
    result = await db.venues.insert_one(venue.dict())
    return {"id": str(result.inserted_id)}

@app.get("/venues")
async def get_venues():
    venues = await db.venues.find().to_list(100)
    for v in venues:
        v["_id"] = str(v["_id"])
    return venues

# BOOKINGS
@app.post("/bookings")
async def create_booking(booking: Booking):
    result = await db.bookings.insert_one(booking.dict())
    return {"id": str(result.inserted_id)}

@app.get("/bookings")
async def get_bookings():
    bookings = await db.bookings.find().to_list(100)
    for b in bookings:
        b["_id"] = str(b["_id"])
    return bookings

# -------------------- FILE UPLOADS --------------------

@app.post("/events/{event_id}/poster")
async def upload_event_poster(event_id: str, file: UploadFile = File(...)):
    content = await file.read()
    result = await db.event_posters.insert_one({
        "event_id": event_id,
        "filename": file.filename,
        "content_type": file.content_type,
        "content": content,
        "uploaded_at": datetime.utcnow()
    })
    return {"file_id": str(result.inserted_id)}

@app.get("/event_posters/{file_id}")
async def get_event_poster(file_id: str):
    doc = await get_file_or_404(db.event_posters, file_id)
    return StreamingResponse(
        io.BytesIO(doc["content"]),
        media_type=doc["content_type"]
    )

@app.post("/events/{event_id}/promo-video")
async def upload_promo_video(event_id: str, file: UploadFile = File(...)):
    content = await file.read()
    result = await db.promo_videos.insert_one({
        "event_id": event_id,
        "filename": file.filename,
        "content_type": file.content_type,
        "content": content,
        "uploaded_at": datetime.utcnow()
    })
    return {"file_id": str(result.inserted_id)}

@app.get("/promo_videos/{file_id}")
async def get_promo_video(file_id: str):
    doc = await get_file_or_404(db.promo_videos, file_id)
    return StreamingResponse(
        io.BytesIO(doc["content"]),
        media_type=doc["content_type"]
    )

@app.post("/venues/{venue_id}/photo")
async def upload_venue_photo(venue_id: str, file: UploadFile = File(...)):
    content = await file.read()
    result = await db.venue_photos.insert_one({
        "venue_id": venue_id,
        "filename": file.filename,
        "content_type": file.content_type,
        "content": content,
        "uploaded_at": datetime.utcnow()
    })
    return {"file_id": str(result.inserted_id)}

@app.get("/venue_photos/{file_id}")
async def get_venue_photo(file_id: str):
    doc = await get_file_or_404(db.venue_photos, file_id)
    return StreamingResponse(
        io.BytesIO(doc["content"]),
        media_type=doc["content_type"]
    )
