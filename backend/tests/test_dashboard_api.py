from app.api.v1.dashboard import get_dashboard
from app.database.models.doc_impact import DocImpact
from app.database.models.doc_pr import DocPR
from app.database.models.project import Project
from app.database.models.scanned_commit import ScannedCommit


def test_dashboard_counts_impacts_commits_and_doc_prs(db_session):
    project = Project(
        name="dashboard-target",
        repo_url="/tmp/dashboard-target",
        provider="local",
        local_path="/tmp/dashboard-target",
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

    db_session.add_all(
        [
            DocImpact(
                commit_id=commit.id,
                document_path="docs/auth.md",
                module_name="auth",
                impact_level="high",
                confidence=0.9,
                status="pending_analysis",
            ),
            DocImpact(
                commit_id=commit.id,
                document_path="docs/api.md",
                module_name="api",
                impact_level="medium",
                confidence=0.7,
                status="pr_merged",
            ),
        ]
    )
    db_session.add_all(
        [
            DocPR(
                project_id=project.id,
                provider="gitea",
                branch_name="doc-watcher/update-auth-a1b2c3d",
                base_branch="main",
                status="open",
            ),
            DocPR(
                project_id=project.id,
                provider="gitea",
                branch_name="doc-watcher/update-api-a1b2c3d",
                base_branch="main",
                status="merged",
            ),
            DocPR(
                project_id=project.id,
                provider="gitea",
                branch_name="doc-watcher/update-old-a1b2c3d",
                base_branch="main",
                status="closed",
            ),
        ]
    )
    db_session.commit()

    dashboard = get_dashboard(project.id, db_session)

    assert dashboard["stats"]["commits_scanned"] == 1
    assert dashboard["stats"]["pending_analysis"] == 1
    assert dashboard["stats"]["pr_merged"] == 1
    assert dashboard["stats"]["high_risk"] == 1
    assert dashboard["stats"]["total_doc_prs"] == 3
    assert dashboard["stats"]["prs_open"] == 1
    assert dashboard["stats"]["prs_merged"] == 1
    assert dashboard["stats"]["prs_rejected"] == 1
    assert len(dashboard["recent_activity"]) == 2
