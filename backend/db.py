import os 
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# simple local SQLite databse (file lives next to this code file)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./kyu_ar.db")

# needed for SQLite + threads on windows 
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
