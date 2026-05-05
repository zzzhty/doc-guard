from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.services.patch_service import PatchService

router = APIRouter()


@router.post("/{project_id}/impacts/{impact_id}/patches")
async def generate_patch(
    project_id: int,
    impact_id: int,
    change_type: str = Query(default="update_section"),
    db: Session = Depends(get_db),
):
    svc = PatchService(db)
    try:
        patch = await svc.generate_patch(impact_id, change_type)
        return _patch_response(patch)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Patch generation failed: {str(e)}")


@router.get("/patches/{patch_id}")
def get_patch(patch_id: int, db: Session = Depends(get_db)):
    svc = PatchService(db)
    patch = svc.get_patch(patch_id)
    if not patch:
        raise HTTPException(status_code=404, detail="Patch not found")
    return _patch_response(patch)


@router.put("/patches/{patch_id}")
def update_patch(patch_id: int, data: dict, db: Session = Depends(get_db)):
    svc = PatchService(db)
    patch = svc.update_patch(patch_id, data.get("patched_content", ""))
    if not patch:
        raise HTTPException(status_code=404, detail="Patch not found")
    return _patch_response(patch)


@router.post("/patches/{patch_id}/approve")
def approve_patch(patch_id: int, db: Session = Depends(get_db)):
    svc = PatchService(db)
    try:
        patch = svc.approve_patch(patch_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not patch:
        raise HTTPException(status_code=404, detail="Patch not found")
    return _patch_response(patch)


@router.post("/patches/{patch_id}/reject")
def reject_patch(patch_id: int, db: Session = Depends(get_db)):
    svc = PatchService(db)
    patch = svc.reject_patch(patch_id)
    if not patch:
        raise HTTPException(status_code=404, detail="Patch not found")
    return _patch_response(patch)


def _patch_response(patch):
    return {
        "id": patch.id,
        "doc_impact_id": patch.doc_impact_id,
        "document_path": patch.document_path,
        "change_type": patch.change_type,
        "original_content": patch.original_content,
        "patched_content": patch.patched_content,
        "diff": patch.diff,
        "quality_report": patch.quality_report,
        "status": patch.status,
    }
