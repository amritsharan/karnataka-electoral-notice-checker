from sqlalchemy import create_engine
from sqlalchemy import text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import logging
from .config import settings

logger = logging.getLogger(__name__)

DB_DRIVE_ID = "1W1UszGKi1W64Er1g1wxY087FfuQ9PjlP"

if settings.DATABASE_URL.startswith("sqlite"):
    import os, httpx
    db_path = settings._db_path
    if not os.path.exists(db_path) or os.path.getsize(db_path) < 100000000:
        logger.info(f"Database file at {db_path} missing or incomplete. Auto-downloading full 4.42M record database from Google Drive...")
        try:
            direct_url = f"https://drive.usercontent.google.com/download?id={DB_DRIVE_ID}&export=download&confirm=t"
            tmp_db_path = db_path + ".tmp"
            with httpx.stream("GET", direct_url, follow_redirects=True, timeout=300.0) as resp:
                resp.raise_for_status()
                with open(tmp_db_path, "wb") as f:
                    for chunk in resp.iter_bytes(chunk_size=1024 * 1024 * 5):
                        f.write(chunk)
            if os.path.exists(tmp_db_path) and os.path.getsize(tmp_db_path) > 100000000:
                if os.path.exists(db_path):
                    os.remove(db_path)
                os.rename(tmp_db_path, db_path)
                logger.info("Successfully downloaded full pre-indexed 4.42M record database!")
        except Exception as err:
            logger.error(f"Failed to auto-download database from Google Drive: {err}")

# Handle SQLite vs PostgreSQL configuration
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False, "timeout": 60.0}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True
)

if settings.DATABASE_URL.startswith("sqlite"):
    with engine.connect() as conn:
        conn.exec_driver_sql("PRAGMA journal_mode=WAL;")
        conn.exec_driver_sql("PRAGMA busy_timeout=60000;")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def _table_exists(connection, table_name: str) -> bool:
    result = connection.execute(
        text("SELECT name FROM sqlite_master WHERE type='table' AND name=:table_name"),
        {"table_name": table_name},
    )
    return result.first() is not None


def _column_exists(connection, table_name: str, column_name: str) -> bool:
    result = connection.execute(text(f"PRAGMA table_info({table_name})"))
    return any(row[1] == column_name for row in result.fetchall())


def ensure_sqlite_schema():
    if not settings.DATABASE_URL.startswith("sqlite"):
        return

    with engine.begin() as connection:
        if _table_exists(connection, "documents"):
            document_columns = {
                "url": "TEXT",
                "parent_url": "TEXT",
                "checksum": "TEXT",
                "subdistrict": "TEXT",
                "status": "TEXT DEFAULT 'DISCOVERED'",
                "attempt_count": "INTEGER DEFAULT 0",
                "last_error": "TEXT",
            }
            for column_name, column_type in document_columns.items():
                if not _column_exists(connection, "documents", column_name):
                    connection.execute(text(f"ALTER TABLE documents ADD COLUMN {column_name} {column_type}"))

            try:
                if _column_exists(connection, "documents", "url") and _column_exists(connection, "documents", "source_url"):
                    connection.execute(text("UPDATE documents SET url = source_url WHERE url IS NULL OR url = ''"))
                if _column_exists(connection, "documents", "checksum") and _column_exists(connection, "documents", "document_hash"):
                    connection.execute(text("UPDATE documents SET checksum = document_hash WHERE checksum IS NULL OR checksum = ''"))
            except Exception as migrate_err:
                logger.warning(f"Schema migration update note: {migrate_err}")


        if _table_exists(connection, "crawl_logs"):
            crawl_log_columns = {
                "stage": "TEXT DEFAULT 'DISCOVERY'",
                "district": "TEXT",
            }
            for column_name, column_type in crawl_log_columns.items():
                if not _column_exists(connection, "crawl_logs", column_name):
                    connection.execute(text(f"ALTER TABLE crawl_logs ADD COLUMN {column_name} {column_type}"))


ensure_sqlite_schema()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
