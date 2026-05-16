import base64

from app.git_providers import FileChange
from app.git_providers.gitea import GiteaGitProvider


def test_commit_files_updates_existing_file_with_sha_and_creates_new_file():
    provider = GiteaGitProvider(
        base_url="https://git.example.test",
        token="token",
        owner="acme",
        repo="demo",
    )
    calls = []

    def fake_request(method, path, json_data=None):
        calls.append((method, path, json_data))
        if method == "GET" and path == "/contents/docs/existing.md?ref=doc-watcher/test":
            return {"sha": "abc123"}
        if method == "GET" and path == "/contents/docs/new.md?ref=doc-watcher/test":
            raise RuntimeError("not found")
        return {}

    provider._request = fake_request

    result = provider.commit_files(
        "doc-watcher/test",
        "docs: update",
        [
            FileChange(path="docs/existing.md", content="updated"),
            FileChange(path="docs/new.md", content="created"),
        ],
    )

    assert result is True
    assert calls[1][0] == "PUT"
    assert calls[1][1] == "/contents/docs/existing.md"
    assert calls[1][2]["sha"] == "abc123"
    assert base64.b64decode(calls[1][2]["content"]).decode() == "updated"
    assert calls[3][0] == "POST"
    assert calls[3][1] == "/contents/docs/new.md"
    assert "sha" not in calls[3][2]
