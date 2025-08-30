from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from jose import JWTError, jwt
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
import os

# Secret & algorithm for JWT
SECRET_KEY = "secret123"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

app = FastAPI()

# Optional: serve frontend files
if os.path.exists("frontend"):
    app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

# Fake database
fake_users_db = {
    "testuser": {
        "username": "testuser",
        "password": "testpass",  # plain text for demo
    }
}

notes_db = []  # store notes temporarily
next_note_id = 1  # auto-increment id

# Schemas
class Note(BaseModel):
    title: str
    content: str

class NoteOut(Note):
    id: int

class Token(BaseModel):
    access_token: str
    token_type: str

@app.get("/api/")
def read_root():
    return {"message": "Welcome to NotesApp"}

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/token")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.post("/api/token", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = fake_users_db.get(form_data.username)
    if not user or user["password"] != form_data.password:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    access_token = create_access_token(data={"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/notes/", response_model=NoteOut)
def create_note(note: Note, user: str = Depends(get_current_user)):
    global next_note_id
    note_data = note.dict()
    note_data["id"] = next_note_id
    next_note_id += 1
    notes_db.append(note_data)
    return note_data

@app.get("/api/notes/", response_model=list[NoteOut])
def list_notes(user: str = Depends(get_current_user)):
    return notes_db

# For Render: automatic host/port
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
