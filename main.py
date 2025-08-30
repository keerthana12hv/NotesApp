from fastapi import FastAPI, Depends, HTTPException, status, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import HTMLResponse
from jose import JWTError, jwt
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta

# Secret & algorithm for JWT
SECRET_KEY = "secret123"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

app = FastAPI(title="NotesApp")

# Fake user database
fake_users_db = {
    "testuser": {
        "username": "testuser",
        "password": "testpass",  # plain text (for demo)
    }
}

# Temporary notes storage
notes_db: List[dict] = []

# ----------------- Schemas -----------------
class Note(BaseModel):
    id: int
    title: str
    content: str

class Token(BaseModel):
    access_token: str
    token_type: str

# ----------------- HTML Root -----------------
@app.get("/", response_class=HTMLResponse)
def read_root():
    return """
    <h1>NotesApp is running!</h1>
    <p>Visit <a href="/docs">/docs</a> to see the API documentation.</p>
    """

# ----------------- Auth -----------------
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
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

@app.post("/token", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = fake_users_db.get(form_data.username)
    if not user or user["password"] != form_data.password:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    access_token = create_access_token(data={"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}

# ----------------- Notes Endpoints -----------------
@app.post("/notes/")
def create_note(note: Note, user: str = Depends(get_current_user)):
    notes_db.append(note.dict())
    return {"msg": "Note created", "note": note}

@app.get("/notes/")
def list_notes(user: str = Depends(get_current_user)):
    return notes_db
