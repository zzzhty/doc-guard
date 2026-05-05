# 02. Local Readonly Loop

## Goal

让用户能接入一个本地 Git 项目，读取 `docops.yml`、浏览 `docs/wiki` 文档树、扫描 commit，并在 UI 中查看 changed files 和 diff。这一阶段不创建补丁和 PR。

## Current State

后端已有 `ProjectService`、`LocalGitProvider`、`DocScanner`、`CommitScanner` 和 `/projects/{id}/changes` 路由。前端已有项目接入、项目详情和 commit 列表，但没有文档树、文档内容页、change detail 路由入口，也没有持久化 changed files。

## Deliverables

- 本地项目接入时读取并保存 `docops.yml` 快照到 `Project.config_yaml`。
- 扫描 commit 时持久化 changed files，避免每次重新解析 diff。
- 前端项目详情页展示文档树、docops 状态和 commit 扫描入口。
- 前端 commit 列表可以进入 commit detail，查看 metadata、changed files、diff。

## Task Breakdown

### P0

- 在项目创建/同步时调用 `load_docops_from_repo()`；存在时保存原始 YAML 到 `Project.config_yaml`，不存在时标记为 missing。
- 为 `ScannedCommit` 增加 `changed_files_json: Text | None`；响应 schema 暴露 `changed_files: list[str]`。
- 在 `CommitScanner.scan_commit()` 和 `scan_recent()` 中解析 diff，保存 changed files。
- 防止同一 project 重复扫描同一 commit；重复扫描返回已有记录或明确 409/400 错误。
- 给 `ChangeList` 中每行 commit 添加详情链接。
- 在 `App.tsx` 增加 `/projects/:id/changes/:commitId` 路由，并让 `ChangeDetail` 能获得 `projectId`。

### P1

- 前端新增文档树组件，接入 `GET /projects/{id}/docs/tree`。
- 前端新增文档内容查看，接入 `GET /projects/{id}/docs/content?path=...`。
- 项目详情显示 `docops.yml` 是否存在、docs/wiki 目录是否存在、最近同步时间。
- 增加 “Scan Recent” 按钮，调用已有 `/changes/scan-recent`。

## Interfaces

- `CommitResponse` 增加派生字段 `changed_files: list[str]`，后端从 `changed_files_json` 解析。
- `CommitDetailResponse` 保留 `diff: str`，同时返回 `changed_files`。
- `ProjectResponse.config_yaml` 用于判断 docops 是否已读取；前端不直接编辑该字段。
- 文档内容读取保持 `GET /projects/{project_id}/docs/content?path={path}&ref={optional}`。

## Acceptance Criteria

- 用户可以接入本地 Git repo，并看到 docops 状态。
- 用户可以扫描指定 commit 和最近 N 个 commit。
- 用户可以从 commit 列表进入详情页，看到 changed files 和 diff。
- 用户可以浏览 `docs` 和 `wiki` 树，并打开 Markdown/YAML 内容。
- 本阶段所有操作保持只读，不切换目标 repo 分支，不写目标 repo 文件。

## Tests

- local temporary Git repo 测试：创建 commit，扫描后返回 changed files。
- API 测试：项目创建后 `config_yaml` 按真实 `docops.yml` 填充。
- 前端至少通过 `pnpm build` 和 `pnpm lint`。

## Risks

- GitPython diff 字符串格式可能不稳定；changed files 应优先从 diff object 或 commit stats 获取，字符串解析作为 fallback。
- local provider 的 sync 不能假设所有本地 repo 都有 remote。
- 读取文档内容必须限制在目标 repo 内，防止 path traversal。
