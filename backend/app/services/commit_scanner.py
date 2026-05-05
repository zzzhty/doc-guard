import json
from datetime import datetime

from sqlalchemy.orm import Session

from app.database.models.project import Project
from app.database.models.scanned_commit import ScannedCommit
from app.services.project_service import ProjectService


class CommitScanner:
    def __init__(self, db: Session):
        self.db = db

    def scan_commit(self, project_id: int, commit_hash: str) -> ScannedCommit:
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError(f"Project {project_id} not found")

        provider = ProjectService.get_git_provider(project)
        commits = provider.list_commits(project.default_branch, limit=100)

        target = None
        for c in commits:
            if c.hash == commit_hash or c.hash.startswith(commit_hash):
                target = c
                break

        if not target:
            raise ValueError(f"Commit {commit_hash} not found in project {project.name}")

        existing = self._get_existing_commit(project_id, target.hash)
        if existing:
            return existing

        scanned = ScannedCommit(
            project_id=project.id,
            commit_hash=target.hash,
            author=target.author,
            message=target.message[:2000],
            changed_files_json=self._serialize_changed_files(provider, target.hash),
            committed_at=target.committed_at,
            scanned_at=datetime.utcnow(),
            analysis_status="pending",
        )
        self.db.add(scanned)
        self.db.commit()
        self.db.refresh(scanned)
        return scanned

    def scan_recent(self, project_id: int, count: int = 10) -> list[ScannedCommit]:
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError(f"Project {project_id} not found")

        provider = ProjectService.get_git_provider(project)
        commits = provider.list_commits(project.default_branch, limit=count)

        existing_hashes = {
            c.commit_hash
            for c in self.db.query(ScannedCommit)
            .filter(ScannedCommit.project_id == project_id)
            .all()
        }

        new_commits = [c for c in commits if c.hash not in existing_hashes]
        scanned_list = []

        for c in new_commits:
            scanned = ScannedCommit(
                project_id=project.id,
                commit_hash=c.hash,
                author=c.author,
                message=c.message[:2000],
                changed_files_json=self._serialize_changed_files(provider, c.hash),
                committed_at=c.committed_at,
                scanned_at=datetime.utcnow(),
                analysis_status="pending",
            )
            self.db.add(scanned)
            scanned_list.append(scanned)

        self.db.commit()
        return scanned_list

    def get_commits(self, project_id: int) -> list[ScannedCommit]:
        return (
            self.db.query(ScannedCommit)
            .filter(ScannedCommit.project_id == project_id)
            .order_by(ScannedCommit.scanned_at.desc())
            .all()
        )

    def get_commit(self, commit_id: int) -> ScannedCommit | None:
        return self.db.query(ScannedCommit).filter(ScannedCommit.id == commit_id).first()

    def get_commit_diff(self, commit_id: int) -> str:
        scanned = self.get_commit(commit_id)
        if not scanned:
            raise ValueError(f"Commit {commit_id} not found")

        project = self.db.query(Project).filter(Project.id == scanned.project_id).first()
        provider = ProjectService.get_git_provider(project)
        return provider.get_commit_diff(scanned.commit_hash)

    def _get_existing_commit(self, project_id: int, commit_hash: str) -> ScannedCommit | None:
        return (
            self.db.query(ScannedCommit)
            .filter(
                ScannedCommit.project_id == project_id,
                ScannedCommit.commit_hash == commit_hash,
            )
            .first()
        )

    def _serialize_changed_files(self, provider, commit_hash: str) -> str:
        changed_files = self._get_changed_files(provider, commit_hash)
        return json.dumps(changed_files)

    def _get_changed_files(self, provider, commit_hash: str) -> list[str]:
        if hasattr(provider, "get_commit_changed_files"):
            return provider.get_commit_changed_files(commit_hash)
        return self._extract_changed_files_from_diff(provider.get_commit_diff(commit_hash))

    def _extract_changed_files_from_diff(self, diff: str) -> list[str]:
        files = set()
        for line in diff.splitlines():
            if line.startswith("diff --git"):
                parts = line.split()
                if len(parts) >= 4:
                    files.add(parts[3].removeprefix("b/"))
        return sorted(files)
