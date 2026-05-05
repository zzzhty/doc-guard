import os
from datetime import datetime

import git as gitpython

from app.git_providers import CommitInfo, FileChange, FileInfo, GitProvider, PRInfo


class LocalGitProvider(GitProvider):
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        repo = gitpython.Repo(repo_path)
        if repo.bare:
            raise ValueError(f"Repository at {repo_path} is bare")
        self._repo = repo

    def get_repo_info(self) -> dict:
        return {
            "path": self.repo_path,
            "branches": self.list_branches(),
            "active_branch": str(self._repo.active_branch),
            "default_branch": "main",
        }

    def list_branches(self) -> list[str]:
        return [b.name for b in self._repo.branches]

    def list_commits(self, branch: str = "main", limit: int = 50) -> list[CommitInfo]:
        commits = []
        try:
            for c in self._repo.iter_commits(branch, max_count=limit):
                commits.append(
                    CommitInfo(
                        hash=str(c.hexsha),
                        author=str(c.author),
                        message=str(c.message).strip(),
                        committed_at=datetime.fromtimestamp(c.committed_date),
                    )
                )
        except Exception:
            pass
        return commits

    def get_commit_diff(self, commit_hash: str) -> str:
        commit = self._repo.commit(commit_hash)
        if commit.parents:
            parent = commit.parents[0]
            diff = parent.diff(commit, create_patch=True)
        else:
            diff = commit.diff(gitpython.NULL_TREE, create_patch=True)
        return "\n".join(str(d) for d in diff)

    def get_commit_changed_files(self, commit_hash: str) -> list[str]:
        commit = self._repo.commit(commit_hash)
        if commit.parents:
            diff = commit.parents[0].diff(commit)
        else:
            diff = commit.diff(gitpython.NULL_TREE)

        files = set()
        for item in diff:
            path = item.b_path or item.a_path
            if path:
                files.add(path)
        return sorted(files)

    def get_file_content(self, path: str, ref: str | None = None) -> str | None:
        try:
            if ref:
                blob = self._repo.tree(ref) / path
            else:
                blob = self._repo.tree(self._repo.active_branch) / path
            return blob.data_stream.read().decode("utf-8")
        except Exception:
            full_path = os.path.join(self.repo_path, path)
            if os.path.isfile(full_path):
                with open(full_path, encoding="utf-8") as f:
                    return f.read()
            return None

    def list_files(self, path: str = "", ref: str | None = None) -> list[FileInfo]:
        base_dir = os.path.join(self.repo_path, path)
        if not os.path.isdir(base_dir):
            return []
        files = []
        for entry in os.listdir(base_dir):
            full = os.path.join(base_dir, entry)
            files.append(
                FileInfo(
                    path=os.path.join(path, entry),
                    type="dir" if os.path.isdir(full) else "file",
                    size=os.path.getsize(full) if os.path.isfile(full) else 0,
                )
            )
        return files

    def file_exists(self, path: str, ref: str | None = None) -> bool:
        full_path = os.path.join(self.repo_path, path)
        return os.path.exists(full_path)

    def create_branch(self, branch_name: str, base_branch: str) -> bool:
        try:
            base = self._repo.branches[base_branch]
            self._repo.create_head(branch_name, base.commit)
            return True
        except Exception:
            return False

    def commit_files(self, branch: str, message: str, files: list[FileChange]) -> bool:
        try:
            branch_obj = self._repo.branches[branch]
            self._repo.head.reference = branch_obj
            self._repo.head.reset(index=True, working_tree=True)

            for f in files:
                full_path = os.path.join(self.repo_path, f.path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, "w", encoding="utf-8") as fh:
                    fh.write(f.content)
                self._repo.index.add([f.path])

            self._repo.index.commit(message)
            return True
        except Exception:
            return False

    def create_pr(self, title: str, body: str, branch: str, base_branch: str) -> PRInfo:
        raise NotImplementedError("Local provider does not support PR creation. Use GiteaGitProvider.")

    def get_pr(self, pr_number: int) -> PRInfo:
        raise NotImplementedError("Local provider does not support PR operations.")

    def list_prs(self, state: str = "open") -> list[PRInfo]:
        raise NotImplementedError("Local provider does not support PR operations.")

    def close_pr(self, pr_number: int) -> bool:
        raise NotImplementedError("Local provider does not support PR operations.")

    def push_branch(self, branch_name: str, remote: str = "origin") -> bool:
        try:
            origin = self._repo.remote(name=remote)
            origin.push(branch_name)
            return True
        except Exception:
            return False
