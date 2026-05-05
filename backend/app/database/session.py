from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings

engine = create_engine(settings.database_url, echo=False)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from app.database.base import Base

    import app.database.models  # noqa: F401 ensure all models are loaded

    Base.metadata.create_all(bind=engine)
    _apply_lightweight_migrations()


def _apply_lightweight_migrations():
    inspector = inspect(engine)
    if "scanned_commits" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("scanned_commits")}
    if "changed_files_json" not in columns:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE scanned_commits ADD COLUMN changed_files_json TEXT"))
