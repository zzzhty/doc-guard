from app.services.config_parser import load_docops_from_repo, parse_docops


def test_parse_docops_reads_project_docs_git_and_modules():
    config = parse_docops(
        """
project:
  name: example-service
docs:
  root: documentation
  wiki_root: knowledge
  meta_root: metadata
git:
  default_branch: trunk
modules:
  auth:
    owner: backend
    code_paths:
      - src/auth/**
      - tests/auth/**
    docs:
      - docs/api/auth.md
      - docs/architecture/auth.md
"""
    )

    assert config.project_name == "example-service"
    assert config.default_branch == "trunk"
    assert config.docs_root == "documentation"
    assert config.wiki_root == "knowledge"
    assert config.meta_root == "metadata"
    assert config.get_module_for_file("src/auth/token.py") == "auth"
    assert config.get_docs_for_module("auth") == [
        "docs/api/auth.md",
        "docs/architecture/auth.md",
    ]


def test_parse_docops_empty_content_returns_defaults():
    config = parse_docops("")

    assert config.project_name == ""
    assert config.default_branch == "main"
    assert config.docs_root == "docs"
    assert config.wiki_root == "wiki"
    assert config.meta_root == "meta"
    assert config.modules == {}


def test_load_docops_from_repo_returns_none_when_missing(tmp_path):
    assert load_docops_from_repo(str(tmp_path)) is None


def test_load_docops_from_repo_reads_docops_file(tmp_path):
    (tmp_path / "docops.yml").write_text(
        """
project:
  name: loaded-project
modules:
  api:
    owner: backend
    code_paths:
      - app/api/**
    docs:
      - docs/api.md
""",
        encoding="utf-8",
    )

    config = load_docops_from_repo(str(tmp_path))

    assert config is not None
    assert config.project_name == "loaded-project"
    assert config.get_module_for_file("app/api/router.py") == "api"
