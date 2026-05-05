from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.services.doc_pr_service import DocPRService

router = APIRouter()


@router.post("/{project_id}/doc-prs")
async def create_pr(project_id: int, data: dict, db: Session = Depends(get_db)):
    svc = DocPRService(db)
    try:
        doc_pr = await svc.create_pr(project_id, data.get("patch_ids", []))
        return _doc_pr_response(doc_pr)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PR creation failed: {str(e)}")


@router.get("/{project_id}/doc-prs")
def list_prs(project_id: int, db: Session = Depends(get_db)):
    svc = DocPRService(db)
    prs = svc.get_prs_for_project(project_id)
    return {
        "prs": [
            _doc_pr_response(pr)
            for pr in prs
        ],
        "total": len(prs),
    }


@router.get("/doc-prs/{doc_pr_id}")
def get_pr(doc_pr_id: int, db: Session = Depends(get_db)):
    svc = DocPRService(db)
    doc_pr = svc.get_pr(doc_pr_id)
    if not doc_pr:
        raise HTTPException(status_code=404, detail="PR not found")
    items = svc.get_pr_items(doc_pr_id)
    return {
        **_doc_pr_response(doc_pr),
        "items": [
            {
                "id": i.id,
                "document_path": i.document_path,
                "change_type": i.change_type,
                "review_required": i.review_required,
                "status": i.status,
            }
            for i in items
        ],
    }


@router.post("/doc-prs/{doc_pr_id}/refresh")
def refresh_pr(doc_pr_id: int, db: Session = Depends(get_db)):
    svc = DocPRService(db)
    pr = svc.refresh_status(doc_pr_id)
    if not pr:
        raise HTTPException(status_code=404, detail="PR not found")
    return _doc_pr_response(pr)


@router.post("/doc-prs/{doc_pr_id}/close")
def close_pr(doc_pr_id: int, db: Session = Depends(get_db)):
    svc = DocPRService(db)
    pr = svc.close_pr(doc_pr_id)
    if not pr:
        raise HTTPException(status_code=404, detail="PR not found")
    return _doc_pr_response(pr)


def _doc_pr_response(doc_pr):
    return {
        "id": doc_pr.id,
        "project_id": doc_pr.project_id,
        "branch_name": doc_pr.branch_name,
        "base_branch": doc_pr.base_branch,
        "pr_number": doc_pr.pr_number,
        "pr_url": doc_pr.pr_url,
        "title": doc_pr.title,
        "body": doc_pr.body,
        "status": doc_pr.status,
        "source_commit": doc_pr.source_commit,
        "created_at": str(doc_pr.created_at),
        "merged_at": str(doc_pr.merged_at) if doc_pr.merged_at else None,
    }
