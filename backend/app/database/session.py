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
    table_names = inspector.get_table_names()

    if "scanned_commits" in table_names:
        columns = {column["name"] for column in inspector.get_columns("scanned_commits")}
        if "changed_files_json" not in columns:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE scanned_commits ADD COLUMN changed_files_json TEXT"))

    if "projects" in table_names:
        columns = {column["name"] for column in inspector.get_columns("projects")}
        if "auth_token" not in columns:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE projects ADD COLUMN auth_token TEXT"))

    if "doc_prs" in table_names:
        columns = {column["name"] for column in inspector.get_columns("doc_prs")}
        if "body" not in columns:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE doc_prs ADD COLUMN body TEXT"))
