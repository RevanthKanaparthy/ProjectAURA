from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database.db import SessionLocal
from database.models import User
from auth.auth_utils import hash_password, verify_password, create_token
import logging

router = APIRouter(prefix="/auth", tags=["Auth"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/register")
def register(name: str, email: str, password: str, role: str, db: Session = Depends(get_db)):
    if role not in ["faculty", "admin"]:
        raise HTTPException(status_code=400, detail="Invalid role")
    print(f"Password received for hashing: '{password}', length: {len(password)}")
    try:
        user = User(name=name, email=email, password=hash_password(password), role=role)
        db.add(user)
        db.commit()
        db.refresh(user)
        return {"message": f"User {user.email} registered successfully"}
    except Exception as e:
        logging.error(f"Error during registration: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal server error during registration: {e}")

@router.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    print(f"Attempting login with email: '{request.email}'")
    user = db.query(User).filter(User.email == request.email).first()
    print(f"User from DB: {user}")
    if not user or not verify_password(request.password, user.password):
        print(f"Password verification failed. Provided: '{request.password}', Stored hash: '{user.password if user else 'No user'}'")
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token({"sub": user.email, "role": user.role})
    return {"access_token": token, "role": user.role}