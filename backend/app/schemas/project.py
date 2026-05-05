from datetime import datetime

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    repo_url: str = Field(..., min_length=1, max_length=1024)
    provider: str = Field(default="local", pattern=r"^(local|gitea|gitlab|github)$")
    auth_token: str | None = Field(default=None, max_length=512)
    default_branch: str = Field(default="main", max_length=255)
    local_path: str | None = Field(default=None, max_length=1024)


class ProjectUpdate(BaseModel):
    name: str | None = None
    auth_token: str | None = None
    default_branch: str | None = None


class ProjectResponse(BaseModel):
    id: int
    name: str
    repo_url: str
    provider: str
    local_path: str | None
    default_branch: str
    config_yaml: str | None
    last_synced_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectListResponse(BaseModel):
    projects: list[ProjectResponse]
    total: int
