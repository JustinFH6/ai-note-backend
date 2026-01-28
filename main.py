from typing import List
from fastapi import FastAPI
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

class Note(BaseModel):
    title: str
    content: str

from sqlalchemy import Column, Integer, String

class NoteDB(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    content = Column(String)

app = FastAPI()

# In-memory "database"
notes_db: List[dict] = []

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

@app.get("/notes")
def get_notes():
    return {
        "count": len(notes_db),
        "notes": notes_db
    }

Base.metadata.create_all(bind=engine)