import json
from datetime import datetime

import pytest

from app.config import settings
from app.database.models.doc_impact import DocImpact
from app.database.models.doc_pr import DocPR, DocPRItem
from app.database.models.patch import Patch
from app.database.models.project import Project
from app.database.models.scanned_commit import ScannedCommit
from app.git_providers import PRInfo
from app.services.doc_pr_service import DocPRService
from app.services.project_service import ProjectService


class FakeProvider:
    def __init__(self):
        self.calls = []

    def create_branch(self, branch_name: str, base_branch: str) -> bool:
        self.calls.append(("create_branch", branch_name, base_branch))
        return True

    def commit_files(self, branch: str, message: str, files) -> bool:
        self.calls.append(("commit_files", branch, message, files))
        return True

    def create_pr(self, title: str, body: str, branch: str, base_branch: str) -> PRInfo:
        self.calls.append(("create_pr", title, body, branch, base_branch))
        return PRInfo(
            number=7,
            title=title,
            url="https://git.example.test/acme/demo/pulls/7",
            branch=branch,
            base_branch=base_branch,
            status="open",
        )


class FakeStatusProvider:
    def __init__(self, pr_info: PRInfo):
        self.pr_info = pr_info
        self.closed = False

    def get_pr(self, pr_number: int) -> PRInfo:
        assert pr_number == self.pr_info.number
        return self.pr_info

    def close_pr(self, pr_number: int) -> bool:
        assert pr_number == self.pr_info.number
        self.closed = True
        return True


def create_approved_patch(db_session):
    project = Project(
        name="doc-pr-target",
        repo_url="https://git.example.test/acme/demo.git",
        provider="gitea",
        default_branch="main",
        auth_token="token",
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)

    commit = ScannedCommit(
        project_id=project.id,
        commit_hash="a1b2c3d4e5f6",
        author="Tester",
        message="change auth token flow",
        changed_files_json=json.dumps(["src/auth/token.py"]),
        analysis_status="completed",
    )
    db_session.add(commit)
    db_session.commit()
    db_session.refresh(commit)

    impact = DocImpact(
        commit_id=commit.id,
        document_path="docs/auth.md",
        module_name="auth",
        impact_level="high",
        reason="Auth docs need an update",
        confidence=0.9,
        status="patch_generated",
    )
    db_session.add(impact)
    db_session.commit()
    db_session.refresh(impact)

    patch = Patch(
        doc_impact_id=impact.id,
        document_path="docs/auth.md",
        change_type="update_section",
        original_content="# Auth\nold\n",
        patched_content="# Auth\nnew\n",
        diff="-old\n+new\n",
        quality_report=json.dumps({"issues": [], "overall_score": 91, "requires_review": False}),
        status="approved",
    )
    db_session.add(patch)
    db_session.commit()
    db_session.refresh(patch)

    impact.patch_id = patch.id
    db_session.commit()
    return project, commit, impact, patch


def create_doc_pr_record(db_session):
    project, commit, impact, patch = create_approved_patch(db_session)
    doc_pr = DocPR(
        project_id=project.id,
        provider="gitea",
        pr_number=7,
        pr_url="https://git.example.test/acme/demo/pulls/7",
        branch_name="doc-watcher/update-auth-a1b2c3d",
        base_branch="main",
        source_commit=commit.commit_hash,
        title="[DocWatcher] Update auth documentation",
        body="body",
        status="open",
    )
    db_session.add(doc_pr)
    db_session.commit()
    db_session.refresh(doc_pr)

    item = DocPRItem(
        doc_pr_id=doc_pr.id,
        document_path=patch.document_path,
        patch_id=patch.id,
        change_type=patch.change_type,
        review_required=True,
        status="included",
    )
    db_session.add(item)
    impact.doc_pr_id = doc_pr.id
    impact.status = "pr_created"
    db_session.commit()
    db_session.refresh(item)
    return project, impact, item, doc_pr


@pytest.mark.asyncio
async def test_create_pr_calls_provider_and_persists_relationships(db_session, monkeypatch):
    monkeypatch.setattr(settings, "llm_api_key", "")
    project, commit, impact, patch = create_approved_patch(db_session)
    fake_provider = FakeProvider()
    monkeypatch.setattr(ProjectService, "get_git_provider", staticmethod(lambda _: fake_provider))

    doc_pr = await DocPRService(db_session).create_pr(project.id, [patch.id])

    assert [call[0] for call in fake_provider.calls] == ["create_branch", "commit_files", "create_pr"]
    assert fake_provider.calls[0][1] == "doc-watcher/update-auth-a1b2c3d"
    committed_files = fake_provider.calls[1][3]
    assert committed_files[0].path == "docs/auth.md"
    assert committed_files[0].content == "# Auth\nnew\n"
    assert doc_pr.pr_number == 7
    assert doc_pr.pr_url == "https://git.example.test/acme/demo/pulls/7"
    assert doc_pr.title == "[DocWatcher] Update auth documentation"
    assert "## Source Change" in doc_pr.body
    assert "src/auth/token.py" in doc_pr.body
    assert doc_pr.source_commit == commit.commit_hash

    items = DocPRService(db_session).get_pr_items(doc_pr.id)
    assert len(items) == 1
    assert items[0].patch_id == patch.id
    assert items[0].status == "included"

    db_session.refresh(impact)
    assert impact.doc_pr_id == doc_pr.id
    assert impact.status == "pr_created"


@pytest.mark.asyncio
async def test_create_pr_requires_approved_patches(db_session):
    project, _, _, patch = create_approved_patch(db_session)
    patch.status = "pending"
    db_session.commit()

    with pytest.raises(ValueError, match="approved"):
        await DocPRService(db_session).create_pr(project.id, [patch.id])


@pytest.mark.parametrize(
    ("remote_status", "merged_at", "expected_pr_status", "expected_impact_status", "expected_item_status"),
    [
        ("open", None, "open", "pr_created", "included"),
        ("closed", None, "closed", "pr_rejected", "rejected"),
        ("closed", datetime(2026, 5, 5, 8, 0, 0), "merged", "pr_merged", "merged"),
    ],
)
def test_refresh_status_maps_remote_pr_status(
    db_session,
    monkeypatch,
    remote_status,
    merged_at,
    expected_pr_status,
    expected_impact_status,
    expected_item_status,
):
    _, impact, item, doc_pr = create_doc_pr_record(db_session)
    provider = FakeStatusProvider(
        PRInfo(
            number=7,
            title="Remote title",
            url="https://git.example.test/acme/demo/pulls/7",
            branch=doc_pr.branch_name,
            base_branch="main",
            status=remote_status,
            merged_at=merged_at,
        )
    )
    monkeypatch.setattr(ProjectService, "get_git_provider", staticmethod(lambda _: provider))

    refreshed = DocPRService(db_session).refresh_status(doc_pr.id)

    assert refreshed.status == expected_pr_status
    assert refreshed.title == "Remote title"
    db_session.refresh(impact)
    db_session.refresh(item)
    assert impact.status == expected_impact_status
    assert item.status == expected_item_status


def test_close_pr_calls_provider_and_marks_impacts_rejected(db_session, monkeypatch):
    _, impact, item, doc_pr = create_doc_pr_record(db_session)
    provider = FakeStatusProvider(
        PRInfo(
            number=7,
            title="Remote title",
            url="https://git.example.test/acme/demo/pulls/7",
            branch=doc_pr.branch_name,
            base_branch="main",
            status="open",
        )
    )
    monkeypatch.setattr(ProjectService, "get_git_provider", staticmethod(lambda _: provider))

    closed = DocPRService(db_session).close_pr(doc_pr.id)

    assert provider.closed is True
    assert closed.status == "closed"
    db_session.refresh(impact)
    db_session.refresh(item)
    assert impact.status == "pr_rejected"
    assert item.status == "rejected"
