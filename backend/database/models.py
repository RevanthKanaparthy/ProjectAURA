from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from database.db import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    email = Column(String(120), unique=True, index=True)
    password = Column(String(255))
    role = Column(String(20))  # faculty / admin

class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255))
    uploaded_by = Column(Integer, ForeignKey("users.id"))
    department = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())