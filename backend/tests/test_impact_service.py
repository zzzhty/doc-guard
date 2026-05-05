import json

import pytest
from git import Actor, Repo

from app.config import settings
from app.database.models.project import Project
from app.database.models.scanned_commit import ScannedCommit
from app.services.impact_service import ImpactService


def commit_file(repo: Repo, path: str, content: str, message: str):
    from pathlib import Path

    full_path = Path(repo.working_tree_dir) / path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content, encoding="utf-8")
    repo.index.add([path])
    actor = Actor("Tester", "tester@example.com")
    return repo.index.commit(message, author=actor, committer=actor)


def create_scanned_commit(db_session, repo_path, commit_hash: str, changed_files: list[str]) -> ScannedCommit:
    project = Project(
        name="impact-target",
        repo_url=str(repo_path),
        provider="local",
        local_path=str(repo_path),
        default_branch="main",
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)

    scanned = ScannedCommit(
        project_id=project.id,
        commit_hash=commit_hash,
        author="Tester",
        message="change auth flow",
        changed_files_json=json.dumps(changed_files),
        analysis_status="pending",
    )
    db_session.add(scanned)
    db_session.commit()
    db_session.refresh(scanned)
    return scanned


@pytest.mark.asyncio
async def test_analyze_commit_uses_docops_candidates_without_llm(db_session, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "llm_api_key", "")
    repo = Repo.init(tmp_path, initial_branch="main")
    commit_file(repo, "docs/api/auth.md", "# Auth\n", "add auth docs")
    commit_file(
        repo,
        "docops.yml",
        """
modules:
  auth:
    owner: backend
    code_paths:
      - src/auth/**
    docs:
      - docs/api/auth.md
""",
        "add docops",
    )
    source_commit = commit_file(repo, "src/auth/token.py", "TOKEN = 'new'\n", "change auth")
    scanned = create_scanned_commit(db_session, tmp_path, source_commit.hexsha, ["src/auth/token.py"])

    impacts = await ImpactService(db_session).analyze_commit(scanned.id)
    duplicate = await ImpactService(db_session).analyze_commit(scanned.id)

    assert len(impacts) == 1
    assert duplicate[0].id == impacts[0].id
    assert impacts[0].document_path == "docs/api/auth.md"
    assert impacts[0].module_name == "auth"
    assert impacts[0].impact_level == "medium"
    assert "LLM_API_KEY is not configured" in impacts[0].reason
    assert scanned.analysis_status == "completed"


@pytest.mark.asyncio
async def test_analyze_commit_falls_back_to_path_similarity(db_session, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "llm_api_key", "")
    repo = Repo.init(tmp_path, initial_branch="main")
    commit_file(repo, "docs/auth.md", "# Auth\n", "add auth docs")
    source_commit = commit_file(repo, "src/auth/token.py", "TOKEN = 'new'\n", "change auth")
    scanned = create_scanned_commit(db_session, tmp_path, source_commit.hexsha, ["src/auth/token.py"])

    impacts = await ImpactService(db_session).analyze_commit(scanned.id)

    assert len(impacts) == 1
    assert impacts[0].document_path == "docs/auth.md"
    assert impacts[0].module_name == "general"


@pytest.mark.asyncio
async def test_analyze_commit_with_no_candidates_returns_empty(db_session, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "llm_api_key", "")
    repo = Repo.init(tmp_path, initial_branch="main")
    commit_file(repo, "docs/deploy.md", "# Deploy\n", "add deploy docs")
    source_commit = commit_file(repo, "src/auth/token.py", "TOKEN = 'new'\n", "change auth")
    scanned = create_scanned_commit(db_session, tmp_path, source_commit.hexsha, ["src/auth/token.py"])

    impacts = await ImpactService(db_session).analyze_commit(scanned.id)

    assert impacts == []
    assert scanned.analysis_status == "completed"


def test_update_impact_status_rejects_unknown_status(db_session):
    with pytest.raises(ValueError, match="Unsupported impact status"):
        ImpactService(db_session).update_impact_status(impact_id=1, status="unknown")
