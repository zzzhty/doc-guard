from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.database.models.project import Project
from app.services.doc_scanner import DocScanner
from app.services.project_service import ProjectService

router = APIRouter()


@router.get("/{project_id}/docs/tree")
def get_doc_tree(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    scanner = DocScanner(project.local_path)
    return scanner.get_doc_tree()


@router.get("/{project_id}/docs/content")
def get_doc_content(
    project_id: int,
    path: str = Query(...),
    ref: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if not _is_safe_repo_path(path):
        raise HTTPException(status_code=400, detail="Invalid path")

    provider = ProjectService.get_git_provider(project)
    content = provider.get_file_content(path, ref)
    if content is None:
        raise HTTPException(status_code=404, detail="File not found")
    return {"path": path, "content": content}


def _is_safe_repo_path(path: str) -> bool:
    candidate = Path(path)
    return not candidate.is_absolute() and ".." not in candidate.parts
