from datetime import datetime

import base64
import httpx

from app.git_providers import CommitInfo, FileChange, FileInfo, GitProvider, PRInfo


class GiteaGitProvider(GitProvider):
    def __init__(self, base_url: str, token: str, owner: str, repo: str):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.owner = owner
        self.repo = repo
        self._headers = {
            "Authorization": f"token {token}",
            "Content-Type": "application/json",
        }

    def _api_url(self, path: str) -> str:
        return f"{self.base_url}/api/v1/repos/{self.owner}/{self.repo}{path}"

    def _request(self, method: str, path: str, json_data: dict | None = None) -> dict:
        url = self._api_url(path)
        response = httpx.request(method, url, headers=self._headers, json=json_data, timeout=30)
        response.raise_for_status()
        if response.status_code == 204:
            return {}
        return response.json()

    def get_repo_info(self) -> dict:
        return self._request("GET", "")

    def list_branches(self) -> list[str]:
        data = self._request("GET", "/branches")
        return [b["name"] for b in data]

    def list_commits(self, branch: str = "main", limit: int = 50) -> list[CommitInfo]:
        data = self._request("GET", f"/commits?sha={branch}&limit={limit}")
        return [
            CommitInfo(
                hash=c["sha"],
                author=c["commit"]["author"]["name"],
                message=c["commit"]["message"],
                committed_at=datetime.fromisoformat(
                    c["commit"]["author"]["date"].replace("Z", "+00:00")
                ),
            )
            for c in data
        ]

    def get_commit_diff(self, commit_hash: str) -> str:
        data = self._request("GET", f"/commits/{commit_hash}")
        diff_url = data.get("diff_url", "")
        if diff_url:
            resp = httpx.get(diff_url, headers=self._headers, timeout=30)
            return resp.text
        return ""

    def get_file_content(self, path: str, ref: str | None = None) -> str | None:
        try:
            ref_param = f"?ref={ref}" if ref else ""
            data = self._request("GET", f"/contents/{path}{ref_param}")
            import base64
            content = data.get("content", "")
            if content:
                return base64.b64decode(content).decode("utf-8")
            return None
        except Exception:
            return None

    def list_files(self, path: str = "", ref: str | None = None) -> list[FileInfo]:
        ref_param = f"?ref={ref}" if ref else ""
        data = self._request("GET", f"/contents/{path}{ref_param}")
        if not isinstance(data, list):
            data = [data]
        return [
            FileInfo(
                path=f['path'],
                type=f['type'],
                size=f.get('size', 0),
            )
            for f in data
        ]

    def file_exists(self, path: str, ref: str | None = None) -> bool:
        return self.get_file_content(path, ref) is not None

    def create_branch(self, branch_name: str, base_branch: str) -> bool:
        try:
            base = self._request("GET", f"/branches/{base_branch}")
            sha = base["commit"]["sha"]
            self._request("POST", "/git/refs", {
                "ref": f"refs/heads/{branch_name}",
                "sha": sha,
            })
            return True
        except Exception:
            return False

    def commit_files(self, branch: str, message: str, files: list[FileChange]) -> bool:
        try:
            for f in files:
                content_b64 = base64.b64encode(f.content.encode()).decode()
                payload = {
                    "branch": branch,
                    "content": content_b64,
                    "message": message,
                }
                method = "POST"
                try:
                    current = self._request("GET", f"/contents/{f.path}?ref={branch}")
                    if isinstance(current, dict) and current.get("sha"):
                        payload["sha"] = current["sha"]
                        method = "PUT"
                except Exception:
                    pass

                self._request(method, f"/contents/{f.path}", payload)
            return True
        except Exception:
            return False

    def create_pr(self, title: str, body: str, branch: str, base_branch: str) -> PRInfo:
        data = self._request("POST", "/pulls", {
            "title": title,
            "body": body,
            "head": branch,
            "base": base_branch,
        })
        return PRInfo(
            number=data["number"],
            title=data["title"],
            url=data["html_url"],
            branch=data["head"]["label"],
            base_branch=data["base"]["label"],
            status="open",
            created_at=datetime.fromisoformat(
                data["created_at"].replace("Z", "+00:00")
            ),
        )

    def get_pr(self, pr_number: int) -> PRInfo:
        data = self._request("GET", f"/pulls/{pr_number}")
        return PRInfo(
            number=data["number"],
            title=data["title"],
            url=data["html_url"],
            branch=data["head"]["label"],
            base_branch=data["base"]["label"],
            status=data["state"],
            created_at=datetime.fromisoformat(
                data["created_at"].replace("Z", "+00:00")
            ) if data.get("created_at") else None,
            merged_at=datetime.fromisoformat(
                data["merged_at"].replace("Z", "+00:00")
            ) if data.get("merged_at") else None,
        )

    def list_prs(self, state: str = "open") -> list[PRInfo]:
        data = self._request("GET", f"/pulls?state={state}")
        return [
            PRInfo(
                number=pr["number"],
                title=pr["title"],
                url=pr["html_url"],
                branch=pr["head"]["label"],
                base_branch=pr["base"]["label"],
                status=pr["state"],
            )
            for pr in data
        ]

    def close_pr(self, pr_number: int) -> bool:
        try:
            self._request("PATCH", f"/pulls/{pr_number}", {"state": "closed"})
            return True
        except Exception:
            return False
