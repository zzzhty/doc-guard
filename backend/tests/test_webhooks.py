from app.api.v1.webhooks import handle_gitea_pull_request_event
from app.database.models.doc_impact import DocImpact
from app.database.models.doc_pr import DocPR, DocPRItem
from app.database.models.patch import Patch
from app.database.models.project import Project
from app.database.models.scanned_commit import ScannedCommit


def test_gitea_pull_request_webhook_marks_doc_pr_merged(db_session):
    project = Project(
        name="webhook-target",
        repo_url="https://git.example.test/acme/demo.git",
        provider="gitea",
        default_branch="main",
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)

    commit = ScannedCommit(
        project_id=project.id,
        commit_hash="a1b2c3d4",
        author="Tester",
        message="change auth",
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
        confidence=0.9,
        status="pr_created",
    )
    db_session.add(impact)
    db_session.commit()
    db_session.refresh(impact)

    patch = Patch(
        doc_impact_id=impact.id,
        document_path="docs/auth.md",
        change_type="update_section",
        status="approved",
    )
    db_session.add(patch)
    db_session.commit()
    db_session.refresh(patch)

    doc_pr = DocPR(
        project_id=project.id,
        provider="gitea",
        pr_number=7,
        pr_url="https://git.example.test/acme/demo/pulls/7",
        branch_name="doc-watcher/update-auth-a1b2c3d",
        base_branch="main",
        source_commit=commit.commit_hash,
        title="[DocWatcher] Update auth documentation",
        status="open",
    )
    db_session.add(doc_pr)
    db_session.commit()
    db_session.refresh(doc_pr)

    item = DocPRItem(
        doc_pr_id=doc_pr.id,
        document_path="docs/auth.md",
        patch_id=patch.id,
        change_type="update_section",
        status="included",
    )
    db_session.add(item)
    impact.doc_pr_id = doc_pr.id
    db_session.commit()

    updated = handle_gitea_pull_request_event(
        {
            "action": "closed",
            "pull_request": {
                "number": 7,
                "title": "Remote title",
                "html_url": "https://git.example.test/acme/demo/pulls/7",
                "state": "closed",
                "merged": True,
                "merged_at": "2026-05-05T08:00:00Z",
                "head": {"ref": "doc-watcher/update-auth-a1b2c3d"},
            },
        },
        db_session,
    )

    assert updated is not None
    assert updated.status == "merged"
    assert updated.title == "Remote title"
    db_session.refresh(impact)
    db_session.refresh(item)
    assert impact.status == "pr_merged"
    assert item.status == "merged"
