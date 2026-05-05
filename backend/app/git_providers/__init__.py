from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass
class CommitInfo:
    hash: str
    author: str
    message: str
    committed_at: datetime | None = None


@dataclass
class FileInfo:
    path: str
    type: str  # "file" | "dir"
    size: int = 0


@dataclass
class PRInfo:
    number: int
    title: str
    url: str
    branch: str
    base_branch: str
    status: str
    created_at: datetime | None = None
    merged_at: datetime | None = None


@dataclass
class FileChange:
    path: str
    content: str


class GitProvider(ABC):
    """Abstract interface for all Git providers."""

    @abstractmethod
    def get_repo_info(self) -> dict: ...

    @abstractmethod
    def list_branches(self) -> list[str]: ...

    @abstractmethod
    def list_commits(self, branch: str = "main", limit: int = 50) -> list[CommitInfo]: ...

    @abstractmethod
    def get_commit_diff(self, commit_hash: str) -> str: ...

    @abstractmethod
    def get_file_content(self, path: str, ref: str | None = None) -> str | None: ...

    @abstractmethod
    def list_files(self, path: str = "", ref: str | None = None) -> list[FileInfo]: ...

    @abstractmethod
    def file_exists(self, path: str, ref: str | None = None) -> bool: ...

    @abstractmethod
    def create_branch(self, branch_name: str, base_branch: str) -> bool: ...

    @abstractmethod
    def commit_files(self, branch: str, message: str, files: list[FileChange]) -> bool: ...

    @abstractmethod
    def create_pr(self, title: str, body: str, branch: str, base_branch: str) -> PRInfo: ...

    @abstractmethod
    def get_pr(self, pr_number: int) -> PRInfo: ...

    @abstractmethod
    def list_prs(self, state: str = "open") -> list[PRInfo]: ...

    @abstractmethod
    def close_pr(self, pr_number: int) -> bool: ...
