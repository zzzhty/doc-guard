from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.commit import (
    CommitDetailResponse,
    CommitListResponse,
    CommitResponse,
    CommitScanRecentRequest,
    CommitScanRequest,
)
from app.services.commit_scanner import CommitScanner

router = APIRouter()


@router.get("/{project_id}/changes", response_model=CommitListResponse)
def list_changes(project_id: int, db: Session = Depends(get_db)):
    scanner = CommitScanner(db)
    commits = scanner.get_commits(project_id)
    return CommitListResponse(commits=commits, total=len(commits))


@router.get("/{project_id}/changes/{commit_id}", response_model=CommitDetailResponse)
def get_change(project_id: int, commit_id: int, db: Session = Depends(get_db)):
    scanner = CommitScanner(db)
    commit = scanner.get_commit(commit_id)
    if not commit or commit.project_id != project_id:
        raise HTTPException(status_code=404, detail="Commit not found")
    diff = scanner.get_commit_diff(commit_id)
    result = CommitDetailResponse.model_validate(commit)
    result.diff = diff
    return result


@router.post("/{project_id}/changes/scan", response_model=CommitResponse, status_code=201)
def scan_commit(project_id: int, data: CommitScanRequest, db: Session = Depends(get_db)):
    scanner = CommitScanner(db)
    try:
        commit = scanner.scan_commit(project_id, data.commit_hash)
        return commit
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{project_id}/changes/scan-recent", response_model=CommitListResponse)
def scan_recent(project_id: int, data: CommitScanRecentRequest, db: Session = Depends(get_db)):
    scanner = CommitScanner(db)
    try:
        commits = scanner.scan_recent(project_id, data.count)
        return CommitListResponse(commits=commits, total=len(commits))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
