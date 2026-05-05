from git import Repo

from app.config import settings
from app.database.models.project import Project
from app.git_providers.gitea import GiteaGitProvider
from app.git_providers.local import LocalGitProvider
from app.services.project_service import ProjectService


def test_create_project_stores_docops_yaml(db_session, tmp_path):
    Repo.init(tmp_path, initial_branch="main")
    docops = """
project:
  name: local-docs
modules:
  api:
    owner: backend
    code_paths:
      - app/api/**
    docs:
      - docs/api.md
"""
    (tmp_path / "docops.yml").write_text(docops, encoding="utf-8")

    project = ProjectService(db_session).create_project(
        {
            "name": "local-docs",
            "repo_url": str(tmp_path),
            "provider": "local",
            "local_path": str(tmp_path),
            "default_branch": "main",
        }
    )

    assert project.config_yaml == docops


def test_sync_project_refreshes_docops_yaml_without_remote(db_session, tmp_path):
    Repo.init(tmp_path, initial_branch="main")
    project = Project(
        name="sync-docops",
        repo_url=str(tmp_path),
        provider="local",
        local_path=str(tmp_path),
        default_branch="main",
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)

    (tmp_path / "docops.yml").write_text("project:\n  name: synced\n", encoding="utf-8")

    synced = ProjectService(db_session).sync_project(project.id)

    assert synced is not None
    assert "name: synced" in synced.config_yaml


def test_get_git_provider_returns_local_provider(tmp_path):
    Repo.init(tmp_path, initial_branch="main")
    project = Project(
        name="local-provider",
        repo_url=str(tmp_path),
        provider="local",
        local_path=str(tmp_path),
        default_branch="main",
    )

    provider = ProjectService.get_git_provider(project)

    assert isinstance(provider, LocalGitProvider)
    assert provider.repo_path == str(tmp_path)


def test_get_git_provider_returns_gitea_provider(monkeypatch):
    monkeypatch.setattr(settings, "gitea_token", "env-token")
    monkeypatch.setattr(settings, "gitea_url", "")
    project = Project(
        name="gitea-provider",
        repo_url="https://git.example.test/acme/demo.git",
        provider="gitea",
        default_branch="main",
    )

    provider = ProjectService.get_git_provider(project)

    assert isinstance(provider, GiteaGitProvider)
    assert provider.base_url == "https://git.example.test"
    assert provider.owner == "acme"
    assert provider.repo == "demo"
    assert provider.token == "env-token"
