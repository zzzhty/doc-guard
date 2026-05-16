import re
from dataclasses import dataclass
from pathlib import Path

import yaml

from app.database.models.project import Project


@dataclass
class DocOpsModuleCandidate:
    name: str
    owner: str
    code_paths: list[str]
    docs: list[str]


@dataclass
class DocOpsDraft:
    yaml: str
    modules: list[DocOpsModuleCandidate]
    docs_root: str
    wiki_root: str
    meta_root: str
    warnings: list[str]
    persisted: bool = False


class DocOpsInitializer:
    CODE_SUFFIXES = {
        ".c",
        ".cc",
        ".cpp",
        ".cs",
        ".cts",
        ".go",
        ".h",
        ".hpp",
        ".java",
        ".js",
        ".jsx",
        ".kt",
        ".mjs",
        ".mts",
        ".php",
        ".py",
        ".rb",
        ".rs",
        ".swift",
        ".ts",
        ".tsx",
    }
    DOC_SUFFIXES = {".md", ".mdx", ".rst", ".txt", ".yml", ".yaml"}
    EXCLUDED_ROOTS = {
        ".git",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".tox",
        ".venv",
        "build",
        "coverage",
        "dist",
        "docs",
        "htmlcov",
        "meta",
        "node_modules",
        "site",
        "target",
        "wiki",
        "__pycache__",
    }
    TEST_ROOTS = {"test", "tests", "__tests__", "spec", "specs"}
    FALLBACK_DOCS = (
        "docs/README.md",
        "docs/ARCHITECTURE.md",
        "docs/RUNBOOK.md",
        "docs/MILESTONES.md",
        "docs/INTEGRATION_TESTS.md",
        "docs/DEPLOY.md",
    )

    def generate(self, project: Project) -> DocOpsDraft:
        if not project.local_path:
            raise ValueError("local_path is required to initialize docops")

        repo_path = Path(project.local_path)
        if not repo_path.is_dir():
            raise ValueError(f"Local path does not exist: {project.local_path}")

        docs_root = self._existing_root(repo_path, "docs")
        wiki_root = self._existing_root(repo_path, "wiki")
        meta_root = self._existing_root(repo_path, "meta")
        docs = self._collect_docs(repo_path, docs_root, wiki_root)
        root_modules = self._discover_modules(repo_path)
        test_paths = self._collect_test_paths(repo_path)

        warnings: list[str] = []
        if not docs:
            warnings.append("No documentation files were found under docs/ or wiki/.")
        if not root_modules:
            warnings.append("No code modules were inferred from top-level source directories.")

        modules = [
            self._build_module_candidate(module_name, root_path, docs, test_paths)
            for module_name, root_path in sorted(root_modules.items())
        ]

        raw = {
            "project": {"name": project.name},
            "docs": {
                "root": docs_root,
                "wiki_root": wiki_root,
                "meta_root": meta_root,
            },
            "git": {
                "provider": project.provider,
                "default_branch": project.default_branch,
                "branch_prefix": "doc-watcher/",
                "pr_title_prefix": "[DocWatcher]",
            },
            "write_policy": {
                "code": {"mode": "readonly"},
                "docs": {"mode": "pull_request", "require_review": True},
            },
            "modules": {
                module.name: {
                    "owner": module.owner,
                    "code_paths": module.code_paths,
                    "docs": module.docs,
                }
                for module in modules
            },
        }
        return DocOpsDraft(
            yaml=yaml.safe_dump(raw, sort_keys=False, allow_unicode=True),
            modules=modules,
            docs_root=docs_root,
            wiki_root=wiki_root,
            meta_root=meta_root,
            warnings=warnings,
        )

    def _existing_root(self, repo_path: Path, name: str) -> str:
        return name if (repo_path / name).is_dir() else name

    def _discover_modules(self, repo_path: Path) -> dict[str, str]:
        modules: dict[str, str] = {}
        for child in sorted(repo_path.iterdir()):
            if not child.is_dir() or child.name.startswith("."):
                continue
            if child.name in self.EXCLUDED_ROOTS or child.name in self.TEST_ROOTS:
                continue
            if child.name == "src":
                nested = self._discover_src_children(repo_path, child)
                modules.update(nested)
                if nested:
                    continue
            if self._contains_code(child):
                modules[self._slug(child.name)] = child.name
        return modules

    def _discover_src_children(self, repo_path: Path, src_path: Path) -> dict[str, str]:
        modules: dict[str, str] = {}
        for child in sorted(src_path.iterdir()):
            if child.is_dir() and not child.name.startswith(".") and self._contains_code(child):
                modules[self._slug(child.name)] = str(child.relative_to(repo_path))
        if not modules and self._contains_code(src_path):
            modules["src"] = "src"
        return modules

    def _contains_code(self, directory: Path) -> bool:
        for path in directory.rglob("*"):
            if self._should_skip(path):
                continue
            if path.is_file() and path.suffix.lower() in self.CODE_SUFFIXES:
                return True
        return False

    def _should_skip(self, path: Path) -> bool:
        return any(part in self.EXCLUDED_ROOTS or part in self.TEST_ROOTS for part in path.parts)

    def _collect_docs(self, repo_path: Path, docs_root: str, wiki_root: str) -> dict[str, str]:
        docs: dict[str, str] = {}
        for root in (docs_root, wiki_root):
            root_path = repo_path / root
            if not root_path.is_dir():
                continue
            for path in sorted(root_path.rglob("*")):
                if path.is_file() and path.suffix.lower() in self.DOC_SUFFIXES:
                    rel = self._posix(path.relative_to(repo_path))
                    docs[rel] = self._read_text(path)
        return docs

    def _collect_test_paths(self, repo_path: Path) -> list[str]:
        paths: list[str] = []
        for root_name in self.TEST_ROOTS:
            root = repo_path / root_name
            if not root.is_dir():
                continue
            for path in sorted(root.rglob("*")):
                if path.is_file() and path.suffix.lower() in self.CODE_SUFFIXES:
                    paths.append(self._posix(path.relative_to(repo_path)))
        return paths

    def _build_module_candidate(
        self,
        module_name: str,
        root_path: str,
        docs: dict[str, str],
        test_paths: list[str],
    ) -> DocOpsModuleCandidate:
        code_paths = [f"{root_path}/**"]
        for test_path in test_paths:
            if self._matches_module(test_path, "", module_name):
                code_paths.append(test_path)

        matched_docs = [
            doc_path
            for doc_path, content in docs.items()
            if doc_path != "README.md" and self._matches_module(doc_path, content, module_name)
        ]
        if not matched_docs:
            matched_docs = [doc for doc in self.FALLBACK_DOCS if doc in docs and doc != "README.md"][:3]

        owner = self._infer_owner(module_name)
        return DocOpsModuleCandidate(
            name=module_name,
            owner=owner,
            code_paths=sorted(dict.fromkeys(code_paths)),
            docs=sorted(dict.fromkeys(matched_docs)),
        )

    def _matches_module(self, path: str, content: str, module_name: str) -> bool:
        haystack = self._normalize(f"{path}\n{content[:20000]}")
        return any(token in haystack for token in self._module_terms(module_name))

    def _module_terms(self, module_name: str) -> set[str]:
        normalized = self._normalize(module_name)
        terms = {normalized}
        terms.update(part for part in normalized.split("_") if len(part) >= 3)
        return terms

    def _infer_owner(self, module_name: str) -> str:
        if "front" in module_name or module_name in {"ui", "web"}:
            return "frontend"
        if "back" in module_name or "api" in module_name or "server" in module_name:
            return "backend"
        return "unassigned"

    def _read_text(self, path: Path) -> str:
        try:
            return path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return path.read_text(encoding="utf-8", errors="ignore")

    def _slug(self, value: str) -> str:
        slug = re.sub(r"[^a-zA-Z0-9]+", "_", value).strip("_").lower()
        return slug or "module"

    def _normalize(self, value: str) -> str:
        return re.sub(r"[^a-z0-9]+", "_", value.lower())

    def _posix(self, path: Path) -> str:
        return path.as_posix()
