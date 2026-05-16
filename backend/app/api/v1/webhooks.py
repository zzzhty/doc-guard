import logging
from datetime import datetime

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.database.models.doc_pr import DocPR
from app.services.doc_pr_service import DocPRService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/gitea")
async def gitea_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.json()
    event = request.headers.get("X-Gitea-Event", "unknown")
    logger.info("Received Gitea webhook: event=%s", event)

    if event == "pull_request":
        doc_pr = handle_gitea_pull_request_event(payload, db)
        if doc_pr:
            logger.info("Updated DocWatcher PR %s to %s", doc_pr.id, doc_pr.status)

    return {"status": "received"}


def handle_gitea_pull_request_event(payload: dict, db: Session) -> DocPR | None:
    pr_data = payload.get("pull_request", {})
    branch = pr_data.get("head", {}).get("ref", "")
    if not branch.startswith("doc-watcher/"):
        return None

    doc_pr = (
        db.query(DocPR)
        .filter(DocPR.provider == "gitea", DocPR.branch_name == branch)
        .order_by(DocPR.created_at.desc())
        .first()
    )
    if not doc_pr:
        return None

    merged_at = _parse_datetime(pr_data.get("merged_at"))
    merged = bool(pr_data.get("merged")) or merged_at is not None
    state = pr_data.get("state")
    action = payload.get("action")
    if merged:
        status = "merged"
    elif state == "closed" or action == "closed":
        status = "closed"
    else:
        status = "open"

    return DocPRService(db).apply_remote_status(
        doc_pr=doc_pr,
        status=status,
        merged_at=merged_at,
        pr_url=pr_data.get("html_url"),
        title=pr_data.get("title"),
    )


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


@router.post("/gitlab")
async def gitlab_webhook(request: Request):
    logger.info("Received GitLab webhook: event=%s", request.headers.get("X-Gitlab-Event", "unknown"))
    return {"status": "received"}


@router.post("/github")
async def github_webhook(request: Request):
    logger.info("Received GitHub webhook: event=%s", request.headers.get("X-GitHub-Event", "unknown"))
    return {"status": "received"}
