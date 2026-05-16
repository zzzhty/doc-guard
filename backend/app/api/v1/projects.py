from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.project import (
    DocOpsConfigUpdate,
    DocOpsInitializeRequest,
    DocOpsPreviewResponse,
    ProjectCreate,
    ProjectListResponse,
    ProjectResponse,
    ProjectUpdate,
)
from app.services.docops_initializer import DocOpsDraft
from app.services.project_service import ProjectService

router = APIRouter()


@router.post("", response_model=ProjectResponse, status_code=201)
def create_project(data: ProjectCreate, db: Session = Depends(get_db)):
    svc = ProjectService(db)
    try:
        project = svc.create_project(data.model_dump())
        return project
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=ProjectListResponse)
def list_projects(db: Session = Depends(get_db)):
    svc = ProjectService(db)
    projects = svc.get_projects()
    return ProjectListResponse(projects=projects, total=len(projects))


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: int, db: Session = Depends(get_db)):
    svc = ProjectService(db)
    project = svc.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(project_id: int, data: ProjectUpdate, db: Session = Depends(get_db)):
    svc = ProjectService(db)
    project = svc.update_project(project_id, data.model_dump(exclude_none=True))
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.delete("/{project_id}", status_code=204)
def delete_project(project_id: int, db: Session = Depends(get_db)):
    svc = ProjectService(db)
    if not svc.delete_project(project_id):
        raise HTTPException(status_code=404, detail="Project not found")


@router.post("/{project_id}/docops/preview", response_model=DocOpsPreviewResponse)
def preview_docops(project_id: int, db: Session = Depends(get_db)):
    svc = ProjectService(db)
    try:
        draft = svc.preview_docops_config(project_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not draft:
        raise HTTPException(status_code=404, detail="Project not found")
    return _docops_preview_response(project_id, draft)


@router.post("/{project_id}/docops/initialize", response_model=DocOpsPreviewResponse)
def initialize_docops(
    project_id: int,
    data: DocOpsInitializeRequest | None = None,
    db: Session = Depends(get_db),
):
    svc = ProjectService(db)
    try:
        draft = svc.initialize_docops_config(
            project_id,
            overwrite_existing=data.overwrite_existing if data else False,
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    if not draft:
        raise HTTPException(status_code=404, detail="Project not found")
    return _docops_preview_response(project_id, draft)


@router.put("/{project_id}/docops/config", response_model=ProjectResponse)
def save_docops_config(
    project_id: int,
    data: DocOpsConfigUpdate,
    db: Session = Depends(get_db),
):
    svc = ProjectService(db)
    try:
        project = svc.save_docops_config(project_id, data.config_yaml)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid DocOps config: {e}")
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.post("/{project_id}/sync", response_model=ProjectResponse)
def sync_project(project_id: int, db: Session = Depends(get_db)):
    svc = ProjectService(db)
    project = svc.sync_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


def _docops_preview_response(project_id: int, draft: DocOpsDraft) -> DocOpsPreviewResponse:
    return DocOpsPreviewResponse(
        project_id=project_id,
        yaml=draft.yaml,
        modules=[
            {
                "name": module.name,
                "owner": module.owner,
                "code_paths": module.code_paths,
                "docs": module.docs,
            }
            for module in draft.modules
        ],
        docs_root=draft.docs_root,
        wiki_root=draft.wiki_root,
        meta_root=draft.meta_root,
        warnings=draft.warnings,
        persisted=draft.persisted,
    )
