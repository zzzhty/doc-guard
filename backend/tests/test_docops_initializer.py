import pytest
from git import Repo

from app.database.models.project import Project
from app.services.config_parser import load_docops_for_project, parse_docops
from app.services.docops_initializer import DocOpsInitializer
from app.services.project_service import ProjectService


def test_docops_initializer_generates_candidate_from_repo_shape(tmp_path):
    (tmp_path / "control_plane").mkdir()
    (tmp_path / "control_plane" / "engine.py").write_text("def run(): pass\n", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_control_plane.py").write_text("def test_run(): pass\n", encoding="utf-8")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "ARCHITECTURE.md").write_text(
        "# Architecture\n\nThe control_plane module owns scheduling.\n",
        encoding="utf-8",
    )

    project = Project(
        name="orchestration",
        repo_url=str(tmp_path),
        provider="local",
        local_path=str(tmp_path),
        default_branch="main",
    )

    draft = DocOpsInitializer().generate(project)
    config = parse_docops(draft.yaml)

    assert draft.docs_root == "docs"
    assert [module.name for module in draft.modules] == ["control_plane"]
    assert config.get_module_for_file("control_plane/engine.py") == "control_plane"
    assert config.get_module_for_file("tests/test_control_plane.py") == "control_plane"
    assert config.get_docs_for_module("control_plane") == ["docs/ARCHITECTURE.md"]
    assert "write_policy:" in draft.yaml


def test_initialize_docops_config_persists_generated_yaml(db_session, tmp_path):
    Repo.init(tmp_path, initial_branch="main")
    (tmp_path / "backend").mkdir()
    (tmp_path / "backend" / "api.py").write_text("def handler(): pass\n", encoding="utf-8")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "ARCHITECTURE.md").write_text("backend API docs\n", encoding="utf-8")

    project = Project(
        name="init-docops",
        repo_url=str(tmp_path),
        provider="local",
        local_path=str(tmp_path),
        default_branch="main",
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)

    draft = ProjectService(db_session).initialize_docops_config(project.id)

    assert draft is not None
    assert draft.persisted is True
    db_session.refresh(project)
    assert "backend:" in project.config_yaml
    assert load_docops_for_project(project).get_module_for_file("backend/api.py") == "backend"


def test_initialize_docops_config_requires_overwrite_for_existing_config(db_session, tmp_path):
    Repo.init(tmp_path, initial_branch="main")
    project = Project(
        name="existing-docops",
        repo_url=str(tmp_path),
        provider="local",
        local_path=str(tmp_path),
        default_branch="main",
        config_yaml="project:\n  name: existing\n",
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)

    with pytest.raises(ValueError, match="already exists"):
        ProjectService(db_session).initialize_docops_config(project.id)
