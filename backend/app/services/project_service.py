import os
from datetime import datetime

from sqlalchemy.orm import Session

from app.database.models.project import Project
from app.git_providers.local import LocalGitProvider


class ProjectService:
    def __init__(self, db: Session):
        self.db = db

    def create_project(self, data: dict) -> Project:
        provider = data.get("provider", "local")
        repo_url = data.get("repo_url", "")
        name = data["name"]

        local_path = data.get("local_path")
        if not local_path:
            local_path = os.path.join(os.path.expanduser("~"), ".docguard", "repos", name)

        from git import Repo

        if provider == "local" and not data.get("local_path"):
            raise ValueError("local_path is required for local provider")

        if provider == "local":
            if not os.path.isdir(local_path):
                raise ValueError(f"Local path does not exist: {local_path}")
            Repo(local_path)
        else:
            os.makedirs(local_path, exist_ok=True)
            if not os.listdir(local_path):
                Repo.clone_from(repo_url, local_path)

        project = Project(
            name=name,
            repo_url=repo_url,
            provider=provider,
            local_path=local_path,
            default_branch=data.get("default_branch", "main"),
            last_synced_at=datetime.utcnow(),
        )
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        return project

    def get_projects(self) -> list[Project]:
        return self.db.query(Project).order_by(Project.created_at.desc()).all()

    def get_project(self, project_id: int) -> Project | None:
        return self.db.query(Project).filter(Project.id == project_id).first()

    def update_project(self, project_id: int, data: dict) -> Project | None:
        project = self.get_project(project_id)
        if not project:
            return None
        for key, val in data.items():
            if val is not None:
                setattr(project, key, val)
        project.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(project)
        return project

    def delete_project(self, project_id: int) -> bool:
        project = self.get_project(project_id)
        if not project:
            return False
        self.db.delete(project)
        self.db.commit()
        return True

    def sync_project(self, project_id: int) -> Project | None:
        project = self.get_project(project_id)
        if not project:
            return None
        provider = self._get_git_provider(project)
        if isinstance(provider, LocalGitProvider):
            provider._repo.remote().fetch()
        project.last_synced_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(project)
        return project

    @staticmethod
    def get_git_provider(project: Project) -> LocalGitProvider:
        return LocalGitProvider(project.local_path)

    @staticmethod
    def _get_git_provider(project: Project) -> LocalGitProvider:
        return LocalGitProvider(project.local_path)
