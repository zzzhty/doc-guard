import fnmatch
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel


class ModuleConfig(BaseModel):
    owner: str
    code_paths: list[str] = []
    docs: list[str] = []


class DocOpsConfig(BaseModel):
    project_name: str = ""
    default_branch: str = "main"
    docs_root: str = "docs"
    wiki_root: str = "wiki"
    meta_root: str = "meta"
    modules: dict[str, ModuleConfig] = {}

    def get_module_for_file(self, filepath: str) -> str | None:
        for mod_name, mod_config in self.modules.items():
            for pattern in mod_config.code_paths:
                if fnmatch.fnmatch(filepath, pattern):
                    return mod_name
                if pattern.endswith("**") and filepath.startswith(pattern.rstrip("*")):
                    return mod_name
        return None

    def get_docs_for_module(self, module_name: str) -> list[str]:
        mod = self.modules.get(module_name)
        if not mod:
            return []
        return mod.docs

    def get_all_docs(self) -> list[str]:
        docs = []
        for mod in self.modules.values():
            docs.extend(mod.docs)
        return list(set(docs))


def parse_docops(content: str) -> DocOpsConfig:
    if not content.strip():
        return DocOpsConfig()

    raw = yaml.safe_load(content)
    if not raw:
        return DocOpsConfig()

    modules = {}
    raw_modules = raw.get("modules", {})
    for name, mod_data in raw_modules.items():
        modules[name] = ModuleConfig(
            owner=mod_data.get("owner", ""),
            code_paths=mod_data.get("code_paths", []),
            docs=mod_data.get("docs", []),
        )

    docs = raw.get("docs", {})
    return DocOpsConfig(
        project_name=raw.get("project", {}).get("name", ""),
        default_branch=raw.get("git", {}).get("default_branch", "main"),
        docs_root=docs.get("root", "docs"),
        wiki_root=docs.get("wiki_root", "wiki"),
        meta_root=docs.get("meta_root", "meta"),
        modules=modules,
    )


def load_docops_from_repo(repo_path: str) -> DocOpsConfig | None:
    config_path = Path(repo_path) / "docops.yml"
    if not config_path.exists():
        return None
    return parse_docops(config_path.read_text(encoding="utf-8"))


def load_docops_for_project(project: Any) -> DocOpsConfig | None:
    if getattr(project, "local_path", None):
        config = load_docops_from_repo(project.local_path)
        if config:
            return config

    config_yaml = getattr(project, "config_yaml", None)
    if config_yaml:
        return parse_docops(config_yaml)

    return None
