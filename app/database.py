import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

# Gikuha na gikan sa .env para kung unsay naa sa Render Dashboard, mao ang masunod
DATABASE_URL = os.getenv("DATABASE_URL")

# Sigurohon nato nga mogamit kini sa modernong psycopg (v3) nga drayber
if DATABASE_URL:
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
    elif DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)
    elif "postgresql+psycopg2://" in DATABASE_URL:
        DATABASE_URL = DATABASE_URL.replace("postgresql+psycopg2://", "postgresql+psycopg://", 1)
else:
    # Fallback backup kung pananglitan dili mabasa ang environment variable sa local
    DATABASE_URL = "postgresql+psycopg://avnadmin:AVNS_-ozKOWmdbjipd08cnxt@evsuigp-inquiry-db-testproject2026.a.aivencloud.com:27184/defaultdb?sslmode=require"

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
