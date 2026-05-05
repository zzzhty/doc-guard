from app.services.config_parser import DocOpsConfig, ModuleConfig
from app.services.module_matcher import ModuleMatcher


def make_config() -> DocOpsConfig:
    return DocOpsConfig(
        modules={
            "auth": ModuleConfig(
                owner="backend",
                code_paths=["src/auth/**", "tests/auth/**"],
                docs=["docs/api/auth.md", "docs/architecture/auth.md"],
            ),
            "deploy": ModuleConfig(
                owner="platform",
                code_paths=["Dockerfile", "deploy/**"],
                docs=["docs/deploy/docker.md"],
            ),
        }
    )


def test_match_groups_changed_files_by_module():
    matcher = ModuleMatcher(make_config())

    result = matcher.match(["src/auth/token.py", "tests/auth/test_token.py", "README.md"])

    assert result == {
        "auth": ["src/auth/token.py", "tests/auth/test_token.py"],
    }


def test_find_affected_docs_deduplicates_module_docs():
    matcher = ModuleMatcher(make_config())

    docs = matcher.find_affected_docs(["src/auth/token.py", "src/auth/session.py"])

    assert sorted(docs) == ["docs/api/auth.md", "docs/architecture/auth.md"]


def test_find_candidate_docs_includes_owner_files_and_docs():
    matcher = ModuleMatcher(make_config())

    candidates = matcher.find_candidate_docs(["Dockerfile"])

    assert candidates == [
        {
            "module": "deploy",
            "owner": "platform",
            "changed_files": ["Dockerfile"],
            "candidate_docs": ["docs/deploy/docker.md"],
        }
    ]


def test_no_matches_returns_empty_results():
    matcher = ModuleMatcher(make_config())

    assert matcher.match(["frontend/src/App.tsx"]) == {}
    assert matcher.find_affected_docs(["frontend/src/App.tsx"]) == []
    assert matcher.find_candidate_docs(["frontend/src/App.tsx"]) == []
