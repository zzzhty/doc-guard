import os
from dataclasses import dataclass, field
from pathlib import Path

try:
    import frontmatter
except ImportError:
    frontmatter = None


@dataclass
class DocumentInfo:
    path: str
    title: str = ""
    metadata: dict = field(default_factory=dict)
    size: int = 0


class DocScanner:
    def __init__(self, repo_path: str, docs_root: str = "docs", wiki_root: str = "wiki"):
        self.repo_path = Path(repo_path)
        self.docs_root = docs_root
        self.wiki_root = wiki_root

    def scan_docs(self) -> list[DocumentInfo]:
        docs_path = self.repo_path / self.docs_root
        return self._scan_dir(docs_path)

    def scan_wiki(self) -> list[DocumentInfo]:
        wiki_path = self.repo_path / self.wiki_root
        return self._scan_dir(wiki_path)

    def scan_all(self) -> dict[str, list[DocumentInfo]]:
        return {
            "docs": self.scan_docs(),
            "wiki": self.scan_wiki(),
        }

    def get_doc_tree(self) -> dict:
        docs_path = self.repo_path / self.docs_root
        tree = self._build_tree_dict(docs_path)
        wiki_path = self.repo_path / self.wiki_root
        wiki_tree = self._build_tree_dict(wiki_path) if wiki_path.is_dir() else {}
        return {
            "docs": tree,
            "wiki": wiki_tree,
        }

    def _scan_dir(self, directory: Path) -> list[DocumentInfo]:
        if not directory.is_dir():
            return []
        docs = []
        for root, _dirs, files in os.walk(directory):
            for fname in files:
                if fname.endswith(".md") or fname.endswith(".yml") or fname.endswith(".yaml"):
                    full_path = Path(root) / fname
                    rel_path = str(full_path.relative_to(self.repo_path))
                    info = DocumentInfo(path=rel_path, size=full_path.stat().st_size)
                    if fname.endswith(".md") and frontmatter:
                        try:
                            content = full_path.read_text(encoding="utf-8")
                            post = frontmatter.loads(content)
                            info.title = post.get("title", "")
                            info.metadata = dict(post.metadata)
                        except Exception:
                            pass
                    docs.append(info)
        return docs

    def _build_tree_dict(self, directory: Path) -> dict:
        if not directory.is_dir():
            return {}
        tree = {}
        for entry in sorted(directory.iterdir()):
            rel = str(entry.relative_to(self.repo_path))
            if entry.is_dir():
                tree[rel] = self._build_tree_dict(entry)
            elif entry.suffix in (".md", ".yml", ".yaml"):
                tree[rel] = None
        return tree
