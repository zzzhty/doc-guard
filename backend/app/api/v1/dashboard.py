from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.database.models.doc_impact import DocImpact
from app.database.models.doc_pr import DocPR
from app.database.models.scanned_commit import ScannedCommit

router = APIRouter()


@router.get("/{project_id}")
def get_dashboard(project_id: int, db: Session = Depends(get_db)):
    commit_ids = select(ScannedCommit.id).filter(ScannedCommit.project_id == project_id)

    impacts = db.query(DocImpact).filter(DocImpact.commit_id.in_(commit_ids))

    pending_analysis = impacts.filter(DocImpact.status == "pending_analysis").count()
    patch_generated = impacts.filter(DocImpact.status == "patch_generated").count()
    pr_created = impacts.filter(DocImpact.status == "pr_created").count()
    pr_merged = impacts.filter(DocImpact.status == "pr_merged").count()
    pr_rejected = impacts.filter(DocImpact.status == "pr_rejected").count()
    ignored = impacts.filter(DocImpact.status == "ignored").count()
    false_positive = impacts.filter(DocImpact.status == "false_positive").count()

    high_risk = impacts.filter(
        DocImpact.impact_level == "high",
        DocImpact.status.in_(["pending_analysis", "patch_generated"]),
    ).count()

    prs = db.query(DocPR).filter(DocPR.project_id == project_id)
    total_doc_prs = prs.count()
    prs_open = prs.filter(DocPR.status == "open").count()
    prs_merged = prs.filter(DocPR.status == "merged").count()
    prs_rejected = prs.filter(DocPR.status.in_(["closed", "rejected"])).count()
    commits_scanned = db.query(ScannedCommit).filter(ScannedCommit.project_id == project_id).count()

    recent = (
        impacts.order_by(DocImpact.created_at.desc())
        .limit(10)
        .all()
    )

    return {
        "stats": {
            "pending_analysis": pending_analysis,
            "patch_generated": patch_generated,
            "pr_created": pr_created,
            "pr_merged": pr_merged,
            "pr_rejected": pr_rejected,
            "ignored": ignored,
            "false_positive": false_positive,
            "high_risk": high_risk,
            "commits_scanned": commits_scanned,
            "total_doc_prs": total_doc_prs,
            "prs_open": prs_open,
            "prs_merged": prs_merged,
            "prs_rejected": prs_rejected,
        },
        "recent_activity": [
            {
                "id": i.id,
                "document_path": i.document_path,
                "impact_level": i.impact_level,
                "status": i.status,
                "created_at": str(i.created_at),
            }
            for i in recent
        ],
    }
