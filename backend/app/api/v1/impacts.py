from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.doc_impact import DocImpactListResponse, DocImpactResponse, DocImpactStatusUpdate
from app.services.impact_service import ImpactService

router = APIRouter()


@router.get("/{project_id}/impacts", response_model=DocImpactListResponse)
def list_impacts(
    project_id: int,
    status: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    svc = ImpactService(db)
    impacts = svc.get_impacts(project_id, status)
    return DocImpactListResponse(impacts=impacts, total=len(impacts))


@router.get("/{project_id}/impacts/{impact_id}", response_model=DocImpactResponse)
def get_impact(project_id: int, impact_id: int, db: Session = Depends(get_db)):
    svc = ImpactService(db)
    impact = svc.get_impact(impact_id)
    if not impact:
        raise HTTPException(status_code=404, detail="Impact not found")
    return impact


@router.post("/{project_id}/changes/{commit_id}/analyze", response_model=DocImpactListResponse)
async def analyze_commit(project_id: int, commit_id: int, db: Session = Depends(get_db)):
    svc = ImpactService(db)
    try:
        impacts = await svc.analyze_commit(commit_id)
        return DocImpactListResponse(impacts=impacts, total=len(impacts))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{project_id}/impacts/{impact_id}/status", response_model=DocImpactResponse)
def update_impact_status(
    project_id: int,
    impact_id: int,
    data: DocImpactStatusUpdate,
    db: Session = Depends(get_db),
):
    svc = ImpactService(db)
    try:
        impact = svc.update_impact_status(impact_id, data.status)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not impact:
        raise HTTPException(status_code=404, detail="Impact not found")
    return impact
