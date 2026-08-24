from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# If using SQLite, check_same_thread is required for multi-threaded uvicorn server
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Auto-apply database columns updates for SQLite/PostgreSQL
from sqlalchemy import text
from sqlalchemy.exc import OperationalError, ProgrammingError
for col_name, col_type in [
    ("drive_file_id", "VARCHAR(255)"),
    ("drive_file_name", "VARCHAR(255)"),
    ("drive_file_url", "VARCHAR(500)"),
]:
    try:
        with engine.begin() as conn:
            conn.execute(text(f"ALTER TABLE assignments ADD COLUMN {col_name} {col_type}"))
    except (OperationalError, ProgrammingError) as e:
        err_msg = str(e).lower()
        if "duplicate column" in err_msg or "already exists" in err_msg or "42701" in err_msg:
            pass
        else:
            raise e



def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
