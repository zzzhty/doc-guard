# 05. Gitea PR-First Loop

## Goal

把 approved patches 写入 `docguard/*` 分支，提交 docs/wiki 变更，并在 Gitea 创建真实 PR。完成后，数据库保存 PR number、URL、状态和关联文档项。

## Current State

已完成。`ProjectService.get_git_provider()` 会根据项目 provider 返回 `LocalGitProvider` 或 `GiteaGitProvider`。`DocPRService.create_pr()` 会验证 approved patches、创建 `docguard/*` 分支、提交文档变更、调用 Gitea PR API，并保存 PR number、URL、title、body、status 和关联 items。

## Deliverables

- [x] `ProjectService` 根据 provider 返回 `LocalGitProvider` 或 `GiteaGitProvider`。
- [x] Gitea 项目接入保存可用连接信息，不把 token 返回给前端。
- [x] `DocPRService` 对 Gitea 执行 create branch、commit files、create PR。
- [x] `DocPR` 保存 `pr_number`、`pr_url`、`title`、`body`、`status`、`source_commit`。
- [x] 创建 PR 后更新 related impacts 为 `pr_created`。

## Task Breakdown

### P0

- [x] 为 Gitea 接入定义最小配置：`repo_url` 解析出 base URL、owner、repo；token 来自创建项目请求或环境变量，后端不得在 response 中返回 token。
- [x] 修改 `ProjectService.get_git_provider(project)`：`local` 返回 `LocalGitProvider`，`gitea` 返回 `GiteaGitProvider`。
- [x] 修正 `GiteaGitProvider.commit_files()`：更新已有文件时需要带当前 file sha；新增文件不带 sha。
- [x] `DocPRService.create_pr()` 对 Gitea 调用 provider.create_branch、commit_files、create_pr。
- [x] 将 LLM 生成的 PR body 保存到 `DocPR`；如果模型失败，用 deterministic template fallback。
- [x] 创建 PR 前验证所有 patch 都属于同一 project，且状态为 `approved`。

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

- [x] `ProjectService.get_git_provider()` 单元测试覆盖 local/gitea。
- [x] `DocPRService` 使用 fake provider 测试 create branch、commit files、create pr 调用顺序。
- [x] Gitea provider 文件更新/新增 sha 行为有单元测试；自动测试不依赖真实 Gitea。
- [x] 前端 build/lint 通过。

## Risks

- 不要把 token 存入前端响应或日志。
- Gitea contents API 对更新文件需要 sha，缺失会导致提交失败。
- 多 patch 跨 commit 创建单个 PR 会让 PR 描述含糊；MVP 优先限制单 source commit。
