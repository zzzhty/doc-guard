from git import Actor, Repo

from app.database.models.project import Project
from app.services.commit_scanner import CommitScanner


def commit_file(repo: Repo, path: str, content: str, message: str):
    full_path = repo.working_tree_dir / path if hasattr(repo.working_tree_dir, "__truediv__") else None
    if full_path is None:
        from pathlib import Path

        full_path = Path(repo.working_tree_dir) / path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content, encoding="utf-8")
    repo.index.add([path])
    actor = Actor("Tester", "tester@example.com")
    return repo.index.commit(message, author=actor, committer=actor)


def create_project_for_repo(db_session, repo_path: str) -> Project:
    project = Project(
        name="scan-target",
        repo_url=repo_path,
        provider="local",
        local_path=repo_path,
        default_branch="main",
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


def test_scan_commit_persists_changed_files_and_deduplicates(db_session, tmp_path):
    repo = Repo.init(tmp_path, initial_branch="main")
    commit_file(repo, "README.md", "# Demo\n", "init docs")
    source_commit = commit_file(repo, "src/app.py", "print('hello')\n", "add app")
    project = create_project_for_repo(db_session, str(tmp_path))

    scanner = CommitScanner(db_session)
    scanned = scanner.scan_commit(project.id, source_commit.hexsha[:8])
    duplicate = scanner.scan_commit(project.id, source_commit.hexsha)

    assert scanned.id == duplicate.id
    assert scanned.commit_hash == source_commit.hexsha
    assert scanned.changed_files == ["src/app.py"]


def test_scan_recent_records_changed_files_for_new_commits(db_session, tmp_path):
    repo = Repo.init(tmp_path, initial_branch="main")
    commit_file(repo, "README.md", "# Demo\n", "init docs")
    commit_file(repo, "src/app.py", "print('hello')\n", "add app")
    project = create_project_for_repo(db_session, str(tmp_path))

    commits = CommitScanner(db_session).scan_recent(project.id, count=2)

    assert len(commits) == 2
    assert {tuple(commit.changed_files) for commit in commits} == {
        ("README.md",),
        ("src/app.py",),
    }
