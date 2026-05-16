import json
from types import SimpleNamespace

import pytest
from git import Actor, Repo

from app.config import settings
from app.database.models.doc_impact import DocImpact
from app.database.models.project import Project
from app.database.models.scanned_commit import ScannedCommit
from app.services.patch_service import PatchService


def commit_file(repo: Repo, path: str, content: str, message: str):
    from pathlib import Path

    full_path = Path(repo.working_tree_dir) / path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content, encoding="utf-8")
    repo.index.add([path])
    actor = Actor("Tester", "tester@example.com")
    return repo.index.commit(message, author=actor, committer=actor)


def create_patch_target(db_session, tmp_path, document_content="# Guide\n\n## Auth\nOld auth docs\n"):
    repo = Repo.init(tmp_path, initial_branch="main")
    commit_file(repo, "docs/auth.md", document_content, "add docs")
    source_commit = commit_file(repo, "src/auth/token.py", "TOKEN = 'new'\n", "change auth")

    project = Project(
        name="patch-target",
        repo_url=str(tmp_path),
        provider="local",
        local_path=str(tmp_path),
        default_branch="main",
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)

    scanned = ScannedCommit(
        project_id=project.id,
        commit_hash=source_commit.hexsha,
        author="Tester",
        message="change auth",
        changed_files_json=json.dumps(["src/auth/token.py"]),
        analysis_status="completed",
    )
    db_session.add(scanned)
    db_session.commit()
    db_session.refresh(scanned)

    impact = DocImpact(
        commit_id=scanned.id,
        document_path="docs/auth.md",
        module_name="auth",
        impact_level="medium",
        reason="Auth docs may be stale",
        confidence=0.8,
        status="pending_analysis",
    )
    db_session.add(impact)
    db_session.commit()
    db_session.refresh(impact)
    return impact


@pytest.mark.asyncio
async def test_generate_patch_without_llm_appends_review_section(db_session, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "llm_api_key", "")
    impact = create_patch_target(db_session, tmp_path)

    patch = await PatchService(db_session).generate_patch(impact.id)

    assert patch.change_type == "append_section"
    assert "# Guide" in patch.patched_content
    assert "Old auth docs" in patch.patched_content
    assert "## DocWatcher Review Required" in patch.patched_content
    assert "LLM_API_KEY is not configured" in patch.quality_report
    assert patch.status == "pending"
    assert impact.patch_id == patch.id
    assert impact.status == "patch_generated"


@pytest.mark.asyncio
async def test_generate_patch_replaces_existing_section_with_llm_result(db_session, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "llm_api_key", "test-key")
    impact = create_patch_target(db_session, tmp_path)

    class FakeLLM:
        async def generate_patch(self, context):
            return SimpleNamespace(
                target_section_heading="Auth",
                new_content="New auth docs",
                change_summary="Update auth",
                source_commit_referenced=False,
            )

        async def review_patch(self, original, patched, change_type):
            return SimpleNamespace(issues=[], overall_score=92, requires_review=False)

    monkeypatch.setattr("app.services.patch_service.LLMService", FakeLLM)

    patch = await PatchService(db_session).generate_patch(impact.id)

    assert patch.change_type == "update_section"
    assert "## Auth\nNew auth docs" in patch.patched_content
    assert "Old auth docs" not in patch.patched_content
    assert "# Guide" in patch.patched_content


@pytest.mark.asyncio
async def test_generate_patch_appends_when_llm_section_is_missing(db_session, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "llm_api_key", "test-key")
    impact = create_patch_target(db_session, tmp_path)

    class FakeLLM:
        async def generate_patch(self, context):
            return SimpleNamespace(
                target_section_heading="Missing Section",
                new_content="New missing section docs",
                change_summary="Add missing section",
                source_commit_referenced=False,
            )

        async def review_patch(self, original, patched, change_type):
            return SimpleNamespace(issues=[], overall_score=80, requires_review=True)

    monkeypatch.setattr("app.services.patch_service.LLMService", FakeLLM)

    patch = await PatchService(db_session).generate_patch(impact.id)

    assert patch.change_type == "append_section"
    assert "Old auth docs" in patch.patched_content
    assert "## Missing Section\n\nNew missing section docs" in patch.patched_content


@pytest.mark.asyncio
async def test_update_approve_and_reject_patch_statuses(db_session, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "llm_api_key", "")
    impact = create_patch_target(db_session, tmp_path)
    service = PatchService(db_session)
    patch = await service.generate_patch(impact.id)

    edited = service.update_patch(patch.id, "# Edited\n")
    assert edited.status == "edited"
    assert "-# Guide" in edited.diff
    assert "+# Edited" in edited.diff

    approved = service.approve_patch(patch.id)
    assert approved.status == "approved"

    with pytest.raises(ValueError, match="Patch cannot be approved"):
        service.approve_patch(patch.id)

    rejected = service.reject_patch(patch.id)
    assert rejected.status == "rejected"
