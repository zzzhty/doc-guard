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

截至 2026-05-05，项目已经跑通 MVP 主闭环：接入项目、读取文档、扫描 commit、分析影响、生成并审核 patch、创建 Gitea PR，以及在 PR 合并/关闭后回写状态和看板统计。

已实现：

- 后端 FastAPI 主体、`/api/v1` 路由聚合和 `/health`。
- 项目接入 CRUD，支持 local path 校验和非 local 仓库 clone 的初步逻辑。
- `LocalGitProvider` 支持 commit 列表、diff、文件读取、本地分支和 commit。
- `ProjectService` 会根据 provider 返回 local 或 Gitea provider；Gitea 接入支持从 `repo_url` 解析 base URL、owner、repo，并使用项目 token 或环境变量 token。
- `GiteaGitProvider` 支持创建分支、按 contents API 提交新增/更新文件，并创建 PR。
- `docops.yml` 解析、模块匹配、文档扫描、commit 扫描、impact、patch、Doc PR 模型与服务已有初版。
- 文档影响分析已支持 docops 候选、无 docops 路径相似度降级、重复分析复用结果、无 LLM key 的保守 heuristic 结果。
- 补丁生成已保证输出完整文档，支持章节替换、未命中章节时追加 review section、编辑、approve/reject、质量报告预览和 approved patch 创建 PR。
- `DocPRService` 已能校验 approved patches、限制文档写入路径、创建 `docguard/*` 分支、提交文档修改、创建 Gitea PR、刷新/关闭 PR，并保存 PR number、URL、body 和 items。
- Dashboard API 已统计 commits、impact 状态、高风险文档、open/merged/rejected PR，并提供最近 impact 活动。
- Gitea webhook 可处理 `docguard/*` pull_request 事件，把 merged/closed/open 状态同步到 `DocPR`、`DocPRItem` 和 `DocImpact`。
- 前端已有真实 Dashboard、项目列表、项目接入、项目详情、docops 状态、文档树/内容浏览、commit 扫描列表、commit detail、patch preview 和 Doc PR 管理页。
- 本地只读闭环已支持扫描指定 commit 和最近 commit，并保存 changed files。
- 后端测试覆盖 `docops.yml` 解析、模块匹配、文档工具、扫描、impact、patch、Doc PR、Gitea provider、Dashboard 和 webhook。

Post-MVP 加固项：

- Gitea webhook 需要增加签名校验、事件来源校验和仓库匹配校验。
- local provider 写操作仍会切换目标仓库工作区，产品化前应改为 worktree 或临时 clone。
- GitLab/GitHub provider 仍只保留接口方向，不进入当前 MVP。

## Key Post-MVP Risks

1. **Local Git 写操作副作用**
   当前 local commit 流程会切换目标仓库分支并 reset working tree。产品化前应改为 worktree 或临时 clone。

2. **Webhook 可信度**
   当前 webhook 只按 `docguard/*` 分支和本地 PR 记录匹配事件；后续必须补签名和仓库校验。

3. **真实环境集成**
   自动测试使用 fake provider，不依赖真实 Gitea；上线前仍需要用真实 Gitea 仓库做手动验收。

## Roadmap

详细执行包见 `.codex/mvp-execution/`。高层顺序如下：

| Milestone | 目标 | 完成标志 |
| --- | --- | --- |
| M0 Engineering Baseline | 修复 lint/test 基线 | 已完成：后端 ruff/test 和前端 build/lint 通过 |
| M1 Local Readonly Loop | 本地项目只读闭环 | 已完成：接入项目、读取 docops、浏览 docs/wiki、查看 commit diff |
| M2 Impact Analysis Loop | 文档影响分析 | 已完成：commit detail 可触发分析并展示影响文档、等级、原因 |
| M3 Patch Preview And Quality Gate | 补丁预览与质量门禁 | 已完成：生成完整文档 patch，支持预览、编辑、approve/reject |
| M4 Gitea PR-First Loop | Gitea PR 创建 | 已完成：创建 `docguard/*` 分支、提交文档修改、创建真实 Gitea PR |
| M5 Dashboard And Close Loop | 看板和状态闭环 | 已完成：PR 合并/关闭后更新 impact 状态和 Dashboard |

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

以上 10 项已在当前实现中具备可演示路径；真实 Gitea 仓库仍建议做一次手动集成验收。

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

- `/dashboard`：真实文档债务和 DocGuard PR 状态。
- `/projects`：项目列表。
- `/projects/connect`：连接 local/Gitea 项目。
- `/projects/:id`：项目详情、docops 状态、文档树和 commit 列表。
- `/projects/:id/changes/:commitId`：commit diff、changed files、impact analysis。
- Patch preview：原文、建议结果、diff、质量报告、approve/reject/edit，并可从 approved patch 创建 PR。
- `/projects/:id/doc-prs`：Doc PR 标题、source commit、分支、状态刷新、关闭和 PR URL。

## Development Commands

推荐使用 runtime 脚本一键启动本地前后端：

```bash
./runtime/docguard init
./runtime/docguard start
./runtime/docguard status
./runtime/docguard logs
./runtime/docguard stop
```

runtime 配置保存到 `$HOME/.local/docguard/config.env`，日志保存到 `$HOME/.local/docguard/logs`，pid 文件保存到 `$HOME/.local/docguard/run`。默认后端运行在 `127.0.0.1:8000`，前端运行在 `127.0.0.1:5173`，前端 `/api` 会代理到配置中的后端地址。

如果希望直接执行 `docguard` 命令，可安装用户级软链接：

```bash
./install.sh
docguard start
docguard status
```

默认链接位置是 `$HOME/.local/bin/docguard`。如果 `$HOME/.local/bin` 不在 `PATH`，脚本会打印需要加入 shell 配置的 `export PATH=...`。

可用命令：

- `./runtime/docguard init [--force]`：创建或重置本地 runtime 配置。
- `./runtime/docguard start`：后台启动 backend 和 frontend。
- `./runtime/docguard up`：前台启动 backend 和 frontend，适合 systemd 调用。
- `./runtime/docguard stop`：停止后台进程。
- `./runtime/docguard restart`：重启后台进程。
- `./runtime/docguard status`：查看进程、HTTP 健康状态、配置和日志路径。
- `./runtime/docguard logs [backend|frontend]`：查看日志。
- `./runtime/docguard install-user-bin [--force]`：安装 `docguard` 命令到 `$HOME/.local/bin`。
- `./runtime/docguard uninstall-user-bin`：删除用户级 `docguard` 命令软链接。
- `./runtime/docguard install-user-service`：安装并启动 `systemd --user` 服务。
- `./runtime/docguard uninstall-user-service`：卸载 `systemd --user` 服务。

根目录的 `install.sh` 和 `uninstall.sh` 是对 `runtime/docguard install-user-bin` / `uninstall-user-bin` 的薄封装，便于直接安装或移除 `docguard` 命令。

systemd 自启动：

```bash
./runtime/docguard install-user-service
systemctl --user status docguard.service
```

如需开机后自动拉起 user service，确保系统启用了用户 linger：

```bash
loginctl enable-linger "$USER"
```

手动启动命令仍然可用。

Backend:

```bash
cd backend
uv sync
uv run python -m uvicorn app.main:app --reload
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
- `cd backend && uv run --all-groups python -m pytest`：通过，38 个测试。

## Documentation Map

- `README.md`：项目定位、当前状态、MVP 路线和维护入口。后续优先更新这里。
- `AGENTS.md`：贡献者和 agent 工作约束。
- `.codex/mvp-execution/`：按 milestone 拆分的执行包和验收清单。

不要再新增平行的产品方案文档或进度 review 文档；如果内容属于项目 guide，收口到本 README；如果内容属于具体执行任务，收口到 `.codex/mvp-execution/`。
