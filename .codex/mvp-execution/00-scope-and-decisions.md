# 00. Scope And Decisions

## Goal

本 MVP 的目标是跑通 `README.md` 定义的 PR-first 文档看门狗闭环：

`连接目标项目 -> 扫描已合并 commit -> 判断受影响文档 -> 生成章节级补丁 -> 创建 doc-watcher/* 分支 -> 创建 PR -> 跟踪合并状态 -> 更新看板`

## Current State

已完成 MVP 主闭环。当前代码具备 FastAPI 后端、React 前端、SQLite/SQLAlchemy 模型、LLM agent 分层、local/Gitea provider、impact/patch/doc-pr 服务、Gitea PR 创建、PR 状态回流和 Dashboard 统计。

## In Scope

- 本地 Git 项目接入、读取 `docops.yml`、扫描 commit 和浏览文档。
- 基于 `docops.yml` 和降级召回的文档影响分析。
- 章节级文档 patch 生成、预览、人工编辑、approve/reject。
- Gitea 真实分支、commit、PR 创建和状态刷新。
- 文档债务看板与 DocWatcher PR 管理页。
- 后端最小测试基线和前端现有 build/lint 基线。

## Out Of Scope

- GitLab/GitHub 完整接入。
- 开放 PR/MR 评论或 companion docs PR。
- 自动合并、绕过 review、直接写 main/master。
- 大规模文档重构、删除正式文档、跨仓库 monorepo 复杂权限模型。
- 完整权限系统、多租户、生产级 secret vault。
- Alembic 等正式迁移体系；MVP 可继续使用 SQLite 和 `create_all`，但 schema 变更必须写明本地重建或轻量迁移步骤。

## Locked Decisions

- Provider 路线：先 `local`，再 `gitea`；UI 中 GitLab/GitHub 可以隐藏或标记为暂未支持。
- 触发路线：只做手动扫描 commit 和最近 N 个 commit 扫描；webhook 只用于 PR 状态回流。
- 状态主线：`pending_analysis -> patch_generated -> pr_created -> pr_merged`，旁路状态为 `ignored`、`false_positive`、`pr_rejected`。
- Patch 策略：默认 `update_section`；支持 `append_section`、`create_wiki_note`、`mark_stale` 的最小能力；禁止 `full_rewrite`、`delete_doc`、`bulk_restructure`。
- 前端主路径：`Project Detail -> Change Detail -> Impact List -> Patch Preview -> Create PR -> PR Status`。
- PR 标题格式：`[DocWatcher] Update {module} docs for {change_summary}`。
- 分支格式：`doc-watcher/{action}-{module}-{short_commit}`。

## Shared Acceptance Criteria

- 用户可以用 UI 完成每个阶段的主操作。
- 每次写入目标项目前都有可预览的 diff 和质量检查结果。
- PR 描述包含 source commit、changed files、affected docs、proposed changes、review notes、quality checks。
- 合并或关闭 PR 后，相关 impact 状态会同步更新。
