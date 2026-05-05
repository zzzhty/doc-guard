import logging

from fastapi import APIRouter, Request

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/gitea")
async def gitea_webhook(request: Request):
    payload = await request.json()
    event = request.headers.get("X-Gitea-Event", "unknown")
    logger.info("Received Gitea webhook: event=%s", event)

    if event == "pull_request":
        action = payload.get("action")
        pr_data = payload.get("pull_request", {})
        branch = pr_data.get("head", {}).get("ref", "")
        if branch.startswith("docguard/"):
            logger.info(
                "DocGuard PR %s: action=%s, state=%s",
                pr_data.get("number"),
                action,
                pr_data.get("state"),
            )

    return {"status": "received"}


@router.post("/gitlab")
async def gitlab_webhook(request: Request):
    logger.info("Received GitLab webhook: event=%s", request.headers.get("X-Gitlab-Event", "unknown"))
    return {"status": "received"}


@router.post("/github")
async def github_webhook(request: Request):
    logger.info("Received GitHub webhook: event=%s", request.headers.get("X-GitHub-Event", "unknown"))
    return {"status": "received"}
