from datetime import datetime

from pydantic import BaseModel, Field


class CommitScanRequest(BaseModel):
    commit_hash: str


class CommitScanRecentRequest(BaseModel):
    count: int = 10


class CommitResponse(BaseModel):
    id: int
    project_id: int
    commit_hash: str
    author: str
    message: str
    changed_files: list[str] = Field(default_factory=list)
    committed_at: datetime | None
    scanned_at: datetime | None
    analysis_status: str

    model_config = {"from_attributes": True}


class CommitDetailResponse(CommitResponse):
    diff: str = ""


class CommitListResponse(BaseModel):
    commits: list[CommitResponse]
    total: int
