from typing import List
from fastapi import FastAPI
from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "sqlite:///./notes.db"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()

from sqlalchemy.orm import Session

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def fetch_note_by_id(note_id: int):
    conn = sqlite3.connect("notes.db")
    cursor = conn.cursor()

    cursor.execute("SELECT id, title, content FROM notes WHERE id = ?", (note_id,))
    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None
    
    return {
        "id": row[0],
        "title": row[1],
        "content": row[2]
    }

class Note(BaseModel):
    title: str
    content: str

class NoteOut(BaseModel):
    id: int
    title: str
    content: str

class NotesResponse(BaseModel):
    count: int
    notes: List[NoteOut]


from sqlalchemy import Column, Integer, String

class NoteDB(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    content = Column(String)

app = FastAPI()

#in-memory "database"
notes_db: List[dict] = []

#simple function to manage connections to SQLite database
def get_db_connection():
    return sqlite3.connect("notes.db")

#function to fetch all notes, can be reused anywhere and simplifies the GET /notes endpoint
def fetch_all_notes():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, title, content FROM notes")
    rows = cursor.fetchall()

    conn.close()

    notes = []
    for row in rows:
        notes.append({
            "id": row[0],
            "title": row[1],
            "content": row[2]
        })

    return notes


@app.get("/")
def root():
    return {"message": "Hello from my first backend"}


from fastapi import Depends

@app.post("/upload-note")
def upload_note(note: Note, db: Session = Depends(get_db)):
    db_note = NoteDB(
        title=note.title,
        content=note.content
    )

    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    
    return {
        "status": "success",
        "message": "Note saved to database",
        "note": {
            "id": db_note.id,
            "title": db_note.title,
            "content": db_note.content
        }
    }

import sqlite3
#get all notes
@app.get("/notes", response_model=NotesResponse)
def get_notes():
    notes = fetch_all_notes()
    return {
        "count": len(notes),
        "notes": notes
    }
#get one individual note by searching ID
@app.get("/notes/{note_id}", response_model=NoteOut)
def get_note(note_id: int):
    note = fetch_note_by_id(note_id)

    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    
    return note

Base.metadata.create_all(bind=engine)