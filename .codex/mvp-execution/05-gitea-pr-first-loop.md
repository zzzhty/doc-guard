# 05. Gitea PR-First Loop

## Goal

把 approved patches 写入 `docguard/*` 分支，提交 docs/wiki 变更，并在 Gitea 创建真实 PR。完成后，数据库保存 PR number、URL、状态和关联文档项。

## Current State

`GiteaGitProvider` 类已有接口雏形，但 `ProjectService.get_git_provider()` 总是返回 `LocalGitProvider`。`DocPRService.create_pr()` 当前只创建本地分支和数据库记录，不 push，不调用远端 PR API，也没有保存 PR body。

## Deliverables

- `ProjectService` 根据 provider 返回 `LocalGitProvider` 或 `GiteaGitProvider`。
- Gitea 项目接入需要保存可用连接信息，不把 token 返回给前端。
- `DocPRService` 对 Gitea 执行 create branch、commit files、create PR。
- `DocPR` 保存 `pr_number`、`pr_url`、`title`、`body`、`status`、`source_commit`。
- 创建 PR 后更新 related impacts 为 `pr_created`。

## Task Breakdown

### P0

- 为 Gitea 接入定义最小配置：`repo_url` 解析出 base URL、owner、repo；token 来自创建项目请求或环境变量，后端不得在 response 中返回 token。
- 修改 `ProjectService.get_git_provider(project)`：`local` 返回 `LocalGitProvider`，`gitea` 返回 `GiteaGitProvider`。
- 修正 `GiteaGitProvider.commit_files()`：更新已有文件时需要带当前 file sha；新增文件不带 sha。
- `DocPRService.create_pr()` 对 Gitea 调用 provider.create_branch、commit_files、create_pr。
- 将 LLM 生成的 PR body 保存到 `DocPR`；如果模型失败，用 deterministic template fallback。
- 创建 PR 前验证所有 patch 都属于同一 project，且状态为 `approved`。

### P1

- local provider 创建 doc branch 时不切换用户工作区；改用 temporary clone 或 git worktree。
- PR branch 命名冲突时追加短序号：`docguard/update-auth-a1b2c3d-2`。
- PR 描述包含 changed files；如果 `ScannedCommit.changed_files_json` 已存在，直接使用。
- 为 Gitea close/refresh 增加真实 API 调用。

## Interfaces

- `POST /projects/{project_id}/doc-prs` 接收 `{ "patch_ids": [1, 2] }`。
- 响应返回 `id`、`branch_name`、`title`、`status`、`pr_number`、`pr_url`。
- `DocPR` 模型增加 `body: Text | None`。
- `GET /projects/{project_id}/doc-prs` 列表包含 `pr_url` 和 `source_commit`。
- `GET /doc-prs/{doc_pr_id}` 返回 items 和 PR body。

## Acceptance Criteria

- 用户选择 approved patches 后，可以创建一个 Gitea PR。
- Gitea 仓库出现 `docguard/*` 分支和文档 commit。
- PR 标题符合 `[DocGuard] ...` 格式。
- PR 描述包含 source commit、changed files、affected docs、proposed changes、review notes、quality checks。
- 数据库中 `DocPR` 和 `DocPRItem` 与 patches/impacts 正确关联。

## Tests

- `ProjectService.get_git_provider()` 单元测试覆盖 local/gitea。
- `DocPRService` 使用 fake provider 测试 create branch、commit files、create pr 调用顺序。
- Gitea API 可用时做手动集成测试；自动测试不依赖真实 Gitea。
- 前端 build/lint 通过。

## Risks

- 不要把 token 存入前端响应或日志。
- Gitea contents API 对更新文件需要 sha，缺失会导致提交失败。
- 多 patch 跨 commit 创建单个 PR 会让 PR 描述含糊；MVP 优先限制单 source commit。
