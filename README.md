# DocGuard

DocGuard 是一个 **PR/MR-first 的 AI 文档治理平台**。它不直接修改目标项目主分支，而是在代码变更后只读分析代码和文档，生成可审查的文档补丁，并通过 `docguard/*` 分支和 PR/MR 提交给团队 review。

本文是项目方案、当前进度和执行方向的统一入口。更细的 milestone 执行任务放在 `.codex/mvp-execution/`，旧的初版方案和进度 review 不再单独维护。

## Core Principles

- 代码只读：DocGuard 不修改业务代码，不绕过分支保护。
- 文档可写：只允许修改目标项目中的 `docs/`、`wiki/`、`meta/` 和 `docops.yml` 等文档治理路径。
- 主分支不直写：正式文档必须通过 PR/MR。
- LLM 不直接落主干：LLM 只生成候选变更，最终由人 review。
- Wiki 默认也走 PR：草稿直写只作为后续可配置能力。

## MVP Workflow

MVP 要优先跑通这条闭环：

```text
用户接入 Git 项目
  -> DocGuard 读取 docops.yml
  -> 扫描已合并 commit
  -> 根据 changed files 匹配模块和候选文档
  -> LLM 判断文档影响范围
  -> LLM 生成章节级文档补丁
  -> 系统执行质量检查
  -> 创建 docguard/* 分支
  -> 提交 docs/wiki 修改
  -> 创建 PR/MR
  -> 团队 review 后合并
  -> DocGuard 更新文档债务状态和看板
```

当前主线固定为 **Local -> Gitea**：先补齐本地 Git 项目的只读扫描、影响分析和补丁预览，再接入 Gitea 的真实分支和 PR 创建。GitLab/GitHub 保留接口方向，但不进入当前 MVP。

## Target Repository Contract

DocGuard 默认面向这样的目标项目结构：

```text
my-project/
├── src/
├── tests/
├── docs/
├── wiki/
├── meta/
└── docops.yml
```

默认权限约定：

| 路径 | 用途 | DocGuard 默认权限 |
| --- | --- | --- |
| `src/` | 业务代码 | 只读 |
| `tests/` | 测试代码 | 只读 |
| `docs/` | 正式文档 | 通过 PR/MR 修改 |
| `wiki/` | 开发过程记录、AI 日志、排障记录 | 默认通过 PR/MR |
| `meta/` | 模块映射、规则、负责人 | 通过 PR/MR 修改 |
| `docops.yml` | 项目配置 | 通过 PR/MR 修改 |

`docops.yml` 是 PR-first 模式的核心配置，用于声明项目默认分支、文档根目录、Git provider、写入策略、模块和文档映射。最小示例：

```yaml
project:
  name: example-service
  default_branch: main

docs:
  root: docs
  wiki_root: wiki
  meta_root: meta

git:
  provider: gitea
  default_branch: main
  branch_prefix: docguard/
  pr_title_prefix: "[DocGuard]"

write_policy:
  code:
    mode: readonly
  docs:
    mode: pull_request
    require_review: true

modules:
  auth:
    owner: backend
    code_paths:
      - src/auth/**
      - tests/auth/**
    docs:
      - docs/api/auth.md
      - docs/architecture/auth.md
```

## Current Implementation Status

截至 2026-05-05，项目已经具备基础骨架，但还没有跑通完整 MVP 闭环。

已实现或部分实现：

- 后端 FastAPI 主体、`/api/v1` 路由聚合和 `/health`。
- 项目接入 CRUD，支持 local path 校验和非 local 仓库 clone 的初步逻辑。
- `LocalGitProvider` 支持 commit 列表、diff、文件读取、本地分支和 commit。
- `GiteaGitProvider` 有 API 操作骨架，包括分支、文件提交和 PR 创建，但尚未接入 provider 工厂。
- `docops.yml` 解析、模块匹配、文档扫描、commit 扫描、impact、patch、Doc PR 模型与服务已有初版。
- 文档影响分析已支持 docops 候选、无 docops 路径相似度降级、重复分析复用结果、无 LLM key 的保守 heuristic 结果。
- 补丁生成已保证输出完整文档，支持章节替换、未命中章节时追加 review section、编辑、approve/reject 和质量报告预览。
- 前端已有 Dashboard、项目列表、项目接入、项目详情、docops 状态、文档树/内容浏览、commit 扫描列表和 commit detail。
- 本地只读闭环已支持扫描指定 commit 和最近 commit，并保存 changed files。
- 后端已建立最小测试基线，覆盖 `docops.yml` 解析、模块匹配、文档工具和 `/health`。

主要缺口：

- `ProjectService.get_git_provider()` 目前总是返回 `LocalGitProvider`，Gitea/GitLab/GitHub UI 选项尚不可用。
- 前端仍缺少 PR 管理页。
- Patch 生成存在关键风险：章节内容可能被当成完整文件提交，必须先修复。
- Webhook 只有占位日志，PR 状态无法回流到文档债务看板。
- 后端测试仍偏少，尚未覆盖数据库服务、Git provider 和 LLM fallback 流程。

## Key Risks To Fix First

1. **Patch 覆盖风险**
   `PatchService.generate_patch()` 不能把 LLM 返回的章节片段直接写成完整文档。必须用结构化 patch 或 `apply_patch_to_section()` 合并回原文档。

2. **Provider 工厂未闭环**
   扫描、读取、提交、PR 创建必须通过同一个 provider 抽象。MVP 只要求 `local` 和 `gitea` 可用。

3. **Local Git 写操作副作用**
   当前 local commit 流程会切换目标仓库分支并 reset working tree。产品化前应改为 worktree 或临时 clone。

4. **前端链路不完整**
   后端已有 impact/patch/doc-pr 雏形，但 UI 还不能从扫描一路走到创建 PR。

5. **状态同步不可用**
   `refresh_status()` 当前是 no-op，webhook 未驱动状态更新。

## Roadmap

详细执行包见 `.codex/mvp-execution/`。高层顺序如下：

| Milestone | 目标 | 完成标志 |
| --- | --- | --- |
| M0 Engineering Baseline | 修复 lint/test 基线 | 已完成：后端 ruff/test 和前端 build/lint 通过 |
| M1 Local Readonly Loop | 本地项目只读闭环 | 已完成：接入项目、读取 docops、浏览 docs/wiki、查看 commit diff |
| M2 Impact Analysis Loop | 文档影响分析 | 已完成：commit detail 可触发分析并展示影响文档、等级、原因 |
| M3 Patch Preview And Quality Gate | 补丁预览与质量门禁 | 已完成：生成完整文档 patch，支持预览、编辑、approve/reject |
| M4 Gitea PR-First Loop | Gitea PR 创建 | 创建 `docguard/*` 分支、提交文档修改、创建真实 Gitea PR |
| M5 Dashboard And Close Loop | 看板和状态闭环 | PR 合并/关闭后更新 impact 状态和 Dashboard |

## MVP Acceptance Criteria

MVP 完成时必须可以演示：

1. 接入一个真实 Git 项目。
2. 读取目标项目的代码和文档。
3. 扫描某个代码 commit。
4. 判断受影响文档。
5. 生成章节级文档补丁。
6. 创建 `docguard/*` 分支。
7. 提交 `docs/` 或 `wiki/` 修改。
8. 创建 PR/MR。
9. PR 描述说明来源 commit、影响文档和需要确认的事项。
10. PR 合并后，平台状态自动更新。

## Generated PR Contract

DocGuard 创建的分支命名：

```text
docguard/{action}-{module}-{short_commit}
```

示例：

```text
docguard/update-auth-a1b2c3d
docguard/add-env-docs-b2c3d4e
```

Commit message 示例：

```text
docs(auth): update token refresh documentation

Source commit: a1b2c3d
Generated-by: DocGuard
```

PR 描述必须包含：

- Summary
- Source Change：source commit、commit title、changed files
- Affected Docs
- Proposed Documentation Changes
- Review Notes
- Quality Checks

## Patch Policy

允许的 patch 类型：

- `update_section`：修改已有章节。
- `append_section`：新增章节。
- `add_reference`：增加引用链接。
- `update_metadata`：修改 frontmatter。
- `create_wiki_note`：创建 wiki 草稿。
- `create_doc`：创建正式文档，必须强 review。
- `mark_stale`：标记文档可能过期。

默认禁止：

- `full_rewrite`
- `delete_doc`
- `bulk_restructure`

大规模文档重构必须生成特殊 proposal PR，并标记 `requires_manual_review: true`。

## App Surfaces

MVP 页面目标：

- `/dashboard`：文档债务和 DocGuard PR 状态。
- `/projects`：项目列表。
- `/projects/connect`：连接 local/Gitea 项目。
- `/projects/:id`：项目详情、docops 状态、文档树和 commit 列表。
- `/projects/:id/changes/:commitId`：commit diff、changed files、impact analysis。
- Patch preview：原文、建议结果、diff、质量报告、approve/reject/edit。
- Doc PR 管理：PR 标题、source commit、影响文档、状态、PR URL。

## Development Commands

Backend:

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload
uv run ruff check app tests
uv run --all-groups python -m pytest
```

Frontend:

```bash
cd frontend
pnpm install
pnpm dev
pnpm build
pnpm lint
```

当前验证结果：

- `cd frontend && pnpm build`：通过。
- `cd frontend && pnpm lint`：通过。
- `cd backend && uv run ruff check app tests`：通过。
- `cd backend && uv run --all-groups python -m pytest`：通过，27 个测试。

## Documentation Map

- `README.md`：项目定位、当前状态、MVP 路线和维护入口。后续优先更新这里。
- `AGENTS.md`：贡献者和 agent 工作约束。
- `.codex/mvp-execution/`：按 milestone 拆分的执行包和验收清单。

不要再新增平行的产品方案文档或进度 review 文档；如果内容属于项目 guide，收口到本 README；如果内容属于具体执行任务，收口到 `.codex/mvp-execution/`。
