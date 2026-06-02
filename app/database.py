# database.py
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

# Gi-hardcode ang Service URI gikan sa Aiven, apan gi-usab na daan ngadto sa postgresql+psycopg2://
DATABASE_URL = "postgresql+psycopg2://avnadmin:AVNS_-ozKOWmdbjipd08cnxt@evsuigp-inquiry-db-testproject2026.a.aivencloud.com:27184/defaultdb?sslmode=require"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Paghimo og helper function para sa database session (Dependency)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
