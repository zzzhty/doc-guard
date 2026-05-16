import os
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from app.config import settings
from app.database.models.project import Project
from app.git_providers import GitProvider
from app.git_providers.gitea import GiteaGitProvider
from app.git_providers.local import LocalGitProvider
from app.services.config_parser import load_docops_from_repo, parse_docops
from app.services.docops_initializer import DocOpsDraft, DocOpsInitializer


class ProjectService:
    def __init__(self, db: Session):
        self.db = db

    def create_project(self, data: dict) -> Project:
        provider = data.get("provider", "local")
        repo_url = data.get("repo_url", "")
        name = data["name"]

        local_path = data.get("local_path")
        if not local_path:
            local_path = os.path.join(os.path.expanduser("~"), ".doc-watcher", "repos", name)

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
            auth_token=data.get("auth_token"),
            local_path=local_path,
            default_branch=data.get("default_branch", "main"),
            config_yaml=self._read_docops_yaml(local_path),
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
            try:
                if provider._repo.remotes:
                    provider._repo.remote().fetch()
            except Exception:
                pass
        repo_docops = self._read_docops_yaml(project.local_path)
        if repo_docops is not None:
            project.config_yaml = repo_docops
        project.last_synced_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(project)
        return project

    def preview_docops_config(self, project_id: int) -> DocOpsDraft | None:
        project = self.get_project(project_id)
        if not project:
            return None
        return DocOpsInitializer().generate(project)

    def initialize_docops_config(self, project_id: int, overwrite_existing: bool = False) -> DocOpsDraft | None:
        project = self.get_project(project_id)
        if not project:
            return None
        if project.config_yaml and not overwrite_existing:
            raise ValueError("DocOps config already exists. Set overwrite_existing=true to replace it.")

        draft = DocOpsInitializer().generate(project)
        project.config_yaml = draft.yaml
        project.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(project)
        draft.persisted = True
        return draft

    def save_docops_config(self, project_id: int, config_yaml: str) -> Project | None:
        project = self.get_project(project_id)
        if not project:
            return None
        parse_docops(config_yaml)
        project.config_yaml = config_yaml
        project.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(project)
        return project

    @staticmethod
    def get_git_provider(project: Project) -> GitProvider:
        if project.provider == "local":
            if not project.local_path:
                raise ValueError("local_path is required for local provider")
            return LocalGitProvider(project.local_path)

        if project.provider == "gitea":
            base_url, owner, repo = ProjectService._parse_gitea_repo_url(project.repo_url)
            token = (project.auth_token or settings.gitea_token).strip()
            if not token:
                raise ValueError("Gitea token is required")
            if settings.gitea_url:
                base_url = settings.gitea_url.rstrip("/")
            return GiteaGitProvider(base_url=base_url, token=token, owner=owner, repo=repo)

        raise ValueError(f"{project.provider} provider is not supported in MVP")

    @staticmethod
    def _get_git_provider(project: Project) -> GitProvider:
        return ProjectService.get_git_provider(project)

    @staticmethod
    def _parse_gitea_repo_url(repo_url: str) -> tuple[str, str, str]:
        parsed = urlparse(repo_url)
        if parsed.scheme in {"http", "https"} and parsed.netloc:
            parts = [part for part in parsed.path.strip("/").split("/") if part]
            base_url = f"{parsed.scheme}://{parsed.netloc}"
        elif repo_url.startswith("git@") and ":" in repo_url:
            host, path = repo_url.split(":", 1)
            parts = [part for part in path.strip("/").split("/") if part]
            base_url = settings.gitea_url.rstrip("/") or f"https://{host.removeprefix('git@')}"
        else:
            raise ValueError("Invalid Gitea repo_url")

        if len(parts) < 2:
            raise ValueError("Gitea repo_url must include owner and repo")

        owner = parts[-2]
        repo = parts[-1].removesuffix(".git")
        if not owner or not repo:
            raise ValueError("Gitea repo_url must include owner and repo")
        return base_url.rstrip("/"), owner, repo

    @staticmethod
    def _read_docops_yaml(local_path: str | None) -> str | None:
        if not local_path:
            return None
        if not load_docops_from_repo(local_path):
            return None
        config_path = Path(local_path) / "docops.yml"
        return config_path.read_text(encoding="utf-8")
