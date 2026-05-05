from datetime import datetime

from pydantic import BaseModel


class DocImpactResponse(BaseModel):
    id: int
    commit_id: int
    document_path: str
    module_name: str
    impact_level: str
    reason: str | None
    confidence: float
    patch_id: int | None
    doc_pr_id: int | None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocImpactListResponse(BaseModel):
    impacts: list[DocImpactResponse]
    total: int


class DocImpactStatusUpdate(BaseModel):
    status: str
