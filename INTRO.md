# 更新后的 MVP 方案：PR/MR-first 的 AI 文档治理平台

## 1. 核心定位

这个工具默认不直接修改目标项目主分支，而是作为一个 **文档变更 PR 生成器 + 文档治理看板**。

一句话定义：

> 当目标项目发生代码变更时，DocGuard 只读分析代码，生成结构化文档补丁，并通过新分支 + PR/MR 的方式提交给团队审查。

核心原则：

```text
代码只读
文档可写
主分支不直接写
正式文档必须走 PR/MR
Wiki 草稿可以配置为直接提交或也走 PR/MR
```

---

# 2. 产品介入目标项目的方式

## 默认模式：PR/MR 模式

推荐作为 MVP 唯一默认模式。

```text
目标项目 Git 仓库
    ↓
DocGuard 只读扫描代码 diff
    ↓
分析哪些文档受影响
    ↓
生成文档补丁
    ↓
创建 docguard/* 分支
    ↓
提交 docs/wiki 修改
    ↓
创建 PR/MR
    ↓
团队 review 后合并
```

DocGuard 的身份类似：

```text
Dependabot / Renovate / CI Bot
```

它不会直接改主分支，只会提交可审查的变更请求。

---

# 3. 推荐仓库结构

目标项目内直接维护文档目录：

```text
my-project/
├── src/
├── tests/
├── docs/
│   ├── overview/
│   ├── architecture/
│   ├── api/
│   ├── config/
│   ├── deploy/
│   ├── runbook/
│   └── adr/
│
├── wiki/
│   ├── agent-runs/
│   ├── decisions/
│   ├── experiments/
│   └── troubleshooting/
│
├── meta/
│   ├── modules.yml
│   ├── owners.yml
│   └── doc-rules.yml
│
└── docops.yml
```

其中：

| 路径           | 用途                | DocGuard 默认权限        |
| ------------ | ----------------- | -------------------- |
| `src/`       | 业务代码              | 只读                   |
| `tests/`     | 测试代码              | 只读                   |
| `docs/`      | 正式文档              | 通过 PR/MR 修改          |
| `wiki/`      | 开发过程记录、AI 日志、排障记录 | 默认通过 PR/MR，可配置直接提交草稿 |
| `meta/`      | 模块映射、规则、负责人       | 通过 PR/MR 修改          |
| `docops.yml` | 项目配置              | 通过 PR/MR 修改          |

---

# 4. MVP 最小闭环

MVP 要优先跑通这条链路：

```text
1. 用户接入一个 Git 项目
2. DocGuard 读取 docops.yml
3. DocGuard 扫描某次代码提交或 PR
4. 根据 changed files 匹配模块
5. 找出候选受影响文档
6. LLM 判断文档影响范围
7. LLM 生成章节级文档补丁
8. 系统进行文档质量检查
9. 创建 docguard/* 分支
10. 提交文档修改 commit
11. 创建 PR/MR
12. 用户在 Git 平台 review
13. 合并后 DocGuard 更新文档状态和债务看板
```

核心闭环可以概括为：

```text
代码变更
  → 文档影响分析
  → 文档补丁生成
  → 创建 PR/MR
  → 人工 review
  → 合并
  → 文档债务状态更新
```

---

# 5. 目标项目接入方式

## 5.1 Git Provider 接入

MVP 可以优先支持一种内网 Git 平台，例如：

```text
Gitea
GitLab
GitHub Enterprise
```

如果先做本地 MVP，可以只支持：

```text
本地 Git 仓库路径
+ SSH remote
+ Personal Access Token
```

正式接入时，DocGuard 需要的权限是：

```text
读取仓库内容
读取 commit / diff / branch / PR
创建分支
提交 docs/wiki/meta 修改
创建 PR/MR
评论 PR/MR
读取 PR/MR 合并状态
```

不需要：

```text
直接修改 main/master
修改业务代码
删除分支保护
绕过 review
管理仓库权限
```

---

## 5.2 项目初始化

如果目标项目还没有文档结构，DocGuard 可以先创建一个初始化 PR：

```text
docguard/init-docops
```

这个 PR 新增：

```text
docs/
wiki/
meta/
docops.yml
```

PR 标题：

```text
[DocGuard] Initialize documentation governance structure
```

这样初始化本身也走审查流程。

---

# 6. docops.yml 配置

PR-first 模式下，`docops.yml` 是核心配置。

```yaml
project:
  name: example-service
  default_branch: main

repositories:
  mode: in_repo

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
    allow_full_rewrite: false

  wiki:
    mode: pull_request
    require_review: true

  meta:
    mode: pull_request
    require_review: true

modules:
  auth:
    owner: backend
    code_paths:
      - src/auth/**
      - src/api/routes/auth.py
      - tests/auth/**
    docs:
      - docs/api/auth.md
      - docs/architecture/auth.md
      - docs/runbook/auth-troubleshooting.md

  deploy:
    owner: platform
    code_paths:
      - Dockerfile
      - docker-compose.yml
      - .env.example
      - deploy/**
    docs:
      - docs/deploy/docker.md
      - docs/config/env.md

rules:
  max_doc_words: 1500
  require_source_commit: true
  forbid_full_rewrite_by_default: true
  require_review_for_architecture_docs: true
  require_review_for_api_docs: true
```

这个配置表达清楚几件事：

```text
哪些代码路径属于哪个模块
哪些模块对应哪些文档
哪些路径可以被 DocGuard 修改
修改必须如何进入目标仓库
哪些文档类型需要强制 review
```

---

# 7. PR/MR 工作流设计

## 7.1 代码变更触发

DocGuard 可以通过三种方式触发：

```text
Webhook：push / PR opened / PR updated / PR merged
手动触发：用户在 UI 里选择 commit 或 PR 分析
定时扫描：每天扫描最近 N 个 commit
```

MVP 推荐先做：

```text
手动触发 + 定时扫描
```

后续再接 Webhook。

---

## 7.2 对已合并 commit 的处理

适合初版 MVP。

```text
main 收到新 commit
    ↓
DocGuard 分析该 commit
    ↓
生成文档 PR
```

例如：

```text
source commit:
a1b2c3d refactor auth token refresh flow

DocGuard 创建分支:
docguard/update-auth-docs-a1b2c3d

DocGuard 创建 PR:
[DocGuard] Update auth docs for token refresh changes
```

PR 内容包括：

```text
来源 commit
受影响代码文件
受影响文档
文档补丁摘要
需要人工确认的点
质量检查结果
```

---

## 7.3 对开放 PR/MR 的处理

这部分可以作为 P1，但设计上要预留。

有两种方式：

### 方式 A：在原 PR 下评论

DocGuard 不创建新分支，只在代码 PR 里评论：

```text
本 PR 可能需要同步更新以下文档：
- docs/api/auth.md
- docs/architecture/auth.md

建议补丁已生成：
...
```

优点：

```text
侵入性低
不会产生额外 PR
适合代码 review 阶段提醒
```

缺点：

```text
文档补丁仍需开发者手动应用
```

### 方式 B：创建 companion docs PR

DocGuard 针对当前代码 PR 创建一个配套文档 PR：

```text
code PR:
feature/auth-token-rotation

docs PR:
docguard/docs-for-auth-token-rotation
```

PR 描述中互相关联。

优点：

```text
文档变更可以独立 review
不需要写入开发者分支
```

缺点：

```text
两个 PR 的合并顺序需要管理
```

MVP 建议先做 **已合并 commit → 文档 PR**，后续再支持开放 PR 场景。

---

# 8. PR 内容规范

DocGuard 创建的 PR 应该非常清晰，不能只是“更新文档”。

## PR 标题

```text
[DocGuard] Update auth docs for token refresh changes
```

或者：

```text
[DocGuard] Add env config docs for Redis TTL
```

## PR 描述模板

```markdown
## Summary

This PR updates documentation based on source code changes.

## Source Change

- Source commit: `a1b2c3d`
- Commit title: `refactor auth token refresh flow`
- Changed files:
  - `src/auth/token.py`
  - `src/api/routes/auth.py`
  - `tests/auth/test_token.py`

## Affected Docs

- `docs/api/auth.md`
- `docs/architecture/auth.md`
- `wiki/agent-runs/2026-05-02-auth-refactor.md`

## Proposed Documentation Changes

- Update Token Refresh section
- Add TOKEN_EXPIRED error code
- Clarify refresh token rotation behavior
- Add Agent Run wiki record

## Review Notes

Please confirm:

- Whether refresh token expiration is 14 days
- Whether TOKEN_EXPIRED is a public API error code
- Whether architecture doc should mention token rotation

## Quality Checks

- Full rewrite: no
- Source commit attached: yes
- Duplicate section risk: low
- Requires human review: yes
```

中文团队可以使用中文模板。

---

# 9. 分支和 Commit 规范

## 分支命名

```text
docguard/update-auth-docs-a1b2c3d
docguard/add-env-docs-b2c3d4e
docguard/wiki-agent-run-c3d4e5f
```

格式：

```text
docguard/{action}-{module}-{short_commit}
```

## Commit message

```text
docs(auth): update token refresh documentation

Source commit: a1b2c3d
Generated-by: DocGuard
```

如果包含 Wiki：

```text
wiki(auth): add agent run record for token refactor

Source commit: a1b2c3d
Generated-by: DocGuard
```

如果一次 PR 同时改正式文档和 Wiki，可以有多个 commit：

```text
wiki(auth): add agent run record for token refactor
docs(auth): update token refresh documentation
```

这样 review 时更清楚。

---

# 10. LLM 在 PR-first 模式下的角色

LLM 仍然不直接写主分支。它只负责生成 PR 里的候选变更。

## 10.1 Change Interpreter

理解代码变化：

```text
这次 commit 改了什么？
是否影响用户可见行为？
是否影响 API、配置、部署、架构或排障文档？
```

---

## 10.2 Impact Analyzer

判断受影响文档：

```text
哪些文档可能过期？
哪些文档应该更新？
影响等级是高、中、低？
为什么？
```

---

## 10.3 Patch Writer

生成文档补丁：

```text
只修改目标章节
不整篇重写
不自由创建大量新文档
不加入无法从代码 diff 推导出的事实
```

---

## 10.4 Doc Reviewer

在 PR 创建前检查补丁质量：

```text
是否重复
是否过长
是否写错文档层级
是否包含推测
是否缺少 source commit
是否把实现细节写进 API 文档
```

---

## 10.5 PR Author

生成 PR 描述：

```text
来源 commit
影响范围
变更摘要
需要人工确认的问题
质量检查结果
```

---

# 11. 文档补丁策略

PR-first 模式下，文档补丁更应该小而清晰。

允许的 patch 类型：

```text
update_section      修改已有章节
append_section      新增章节
add_reference       增加引用链接
update_metadata     修改 frontmatter
create_wiki_note    创建 Wiki 草稿
create_doc          创建正式文档，需要强 review
mark_stale          标记文档可能过期
```

默认禁止：

```text
full_rewrite        整篇重写
delete_doc          删除正式文档
bulk_restructure    大规模重构文档结构
```

如果确实需要整篇重构，必须生成特殊 PR：

```text
[DocGuard] Proposal: Restructure auth documentation
```

并标记为：

```text
requires_manual_review: true
large_change: true
```

---

# 12. Wiki 在 PR-first 模式下的处理

Wiki 有两种策略。

## 推荐默认：Wiki 也走 PR

优点：

```text
所有文档变更都有审查记录
不会污染仓库
适合团队项目
```

## 可选模式：Wiki 草稿直接提交到 docguard 分支

例如：

```text
docguard/wiki-drafts
```

或者：

```text
wiki/agent-runs/ 自动创建后仍通过 PR 合并
```

MVP 建议：

```text
正式文档 docs/：必须 PR
Wiki wiki/：默认 PR，可配置直接 commit 到指定 wiki-draft 分支
```

---

# 13. 核心页面更新

## 13.1 文档债务看板

新增 PR 状态：

```text
未处理文档影响：12
已生成待审 PR：4
已合并文档 PR：8
被拒绝文档 PR：2
标记误报：3
高风险过期文档：3
```

每条文档债务状态：

```text
pending_analysis
patch_generated
pr_created
pr_merged
pr_rejected
ignored
false_positive
```

---

## 13.2 变更影响页

展示某个 commit / PR 的文档影响：

```text
source commit: a1b2c3d
changed files:
- src/auth/token.py
- src/api/routes/auth.py

affected docs:
- docs/api/auth.md       high
- docs/architecture/auth.md medium

generated PR:
[DocGuard] Update auth docs for token refresh changes
status: open
```

---

## 13.3 文档补丁预览页

在创建 PR 前预览：

```text
左侧：当前文档
中间：建议补丁
右侧：代码 diff 依据
底部：创建 PR / 编辑补丁 / 忽略
```

---

## 13.4 PR 管理页

展示所有 DocGuard 创建的 PR/MR：

```text
PR 标题
来源 commit
影响模块
修改文档
状态
创建时间
合并时间
reviewer
```

状态：

```text
open
merged
closed
conflict
needs_update
```

---

# 14. 数据模型更新

在原有模型基础上，增加 PR 相关表。

## doc_prs

```sql
CREATE TABLE doc_prs (
    id INTEGER PRIMARY KEY,
    provider TEXT NOT NULL,
    repository TEXT NOT NULL,
    pr_number INTEGER,
    pr_url TEXT,
    branch_name TEXT NOT NULL,
    base_branch TEXT NOT NULL,
    source_commit TEXT,
    title TEXT,
    status TEXT, -- open / merged / closed / conflict / failed
    created_at DATETIME,
    merged_at DATETIME
);
```

## doc_pr_items

```sql
CREATE TABLE doc_pr_items (
    id INTEGER PRIMARY KEY,
    doc_pr_id INTEGER NOT NULL,
    document_path TEXT NOT NULL,
    patch_id INTEGER,
    change_type TEXT,
    review_required BOOLEAN,
    status TEXT
);
```

## doc_impacts 增加字段

```sql
ALTER TABLE doc_impacts ADD COLUMN doc_pr_id INTEGER;
ALTER TABLE doc_impacts ADD COLUMN pr_status TEXT;
```

---

# 15. API 更新

## Git Provider API

```text
POST   /api/repos/connect
GET    /api/repos/status
POST   /api/repos/sync
```

## Change API

```text
GET    /api/changes
POST   /api/changes/analyze
GET    /api/changes/{commit_hash}/impact
```

## Patch API

```text
POST   /api/patches/generate
GET    /api/patches/{id}
POST   /api/patches/{id}/edit
POST   /api/patches/{id}/ignore
```

## PR API

```text
POST   /api/prs/create
GET    /api/prs
GET    /api/prs/{id}
POST   /api/prs/{id}/refresh-status
POST   /api/prs/{id}/close
```

## Webhook API

```text
POST   /api/webhooks/gitea
POST   /api/webhooks/gitlab
POST   /api/webhooks/github
```

MVP 可以先不实现全部 webhook，预留接口即可。

---

# 16. 技术栈更新

## 后端

```text
Python
FastAPI
GitPython
SQLite
SQLAlchemy
Pydantic
markdown-it-py
python-frontmatter
```

Git Provider 集成：

```text
Gitea API / GitLab API / GitHub API
```

MVP 优先建议：

```text
Gitea 或 GitLab 选一个
```

如果你主要在内网：

```text
Gitea 优先
```

因为部署轻量，适合自托管。

---

## 前端

```text
React
TypeScript
Vite
Monaco Editor
Markdown Renderer
shadcn/ui 或 Ant Design
```

新增页面：

```text
/dashboard
/changes
/impacts
/patches
/doc-prs
/docs/:path
/wiki/:path
/settings
```

---

# 17. MVP 阶段计划

## 阶段 1：只读接入目标项目

目标：

```text
连接 Git 仓库
读取 docs/wiki/docops.yml
扫描 commit
展示文档树
```

交付：

```text
项目接入页
文档阅读页
commit 列表
changed files 展示
```

---

## 阶段 2：文档影响分析

目标：

```text
根据 changed files 匹配模块
找候选文档
LLM 判断影响范围
```

交付：

```text
变更影响页
影响等级 high / medium / low
影响原因说明
```

---

## 阶段 3：文档补丁生成

目标：

```text
定位目标章节
生成结构化 patch
进行质量检查
```

交付：

```text
补丁预览页
质量检查报告
人工编辑补丁
忽略 / 标记误报
```

---

## 阶段 4：创建分支和 PR/MR

目标：

```text
创建 docguard/* 分支
写入 docs/wiki 修改
提交 commit
创建 PR/MR
```

交付：

```text
PR 创建功能
PR 描述模板
PR 状态跟踪
文档债务状态更新
```

---

## 阶段 5：看板和闭环

目标：

```text
展示文档债务状态
展示 DocGuard PR 状态
合并后自动更新状态
```

交付：

```text
文档债务看板
DocGuard PR 管理页
已合并 / 已关闭 / 待 review 状态
```

---

# 18. MVP 验收标准

MVP 成功标准：

```text
1. 可以接入一个真实 Git 项目
2. 可以读取目标项目的代码和文档
3. 可以扫描某个代码 commit
4. 可以判断受影响文档
5. 可以生成章节级文档补丁
6. 可以创建 docguard/* 分支
7. 可以提交 docs/wiki 修改
8. 可以创建 PR/MR
9. PR 描述能说明来源 commit、影响文档和需确认事项
10. PR 合并后，平台状态能更新
```

这 10 条跑通，就已经是一个完整 MVP。

---

# 19. 第一版不做什么

PR-first MVP 仍然不要做：

```text
不直接修改主分支
不修改业务代码
不自动合并 PR
不做复杂权限系统
不做多人实时协作
不做完整 RAG
不做自动架构图
不做大规模文档重构
不默认整篇重写文档
```

---

# 20. 最终更新版定义

更新后的 MVP 可以定义为：

> **DocGuard 是一个 PR-first 的 AI-native 文档治理平台。它以只读方式分析目标项目代码变更，识别受影响文档，生成结构化文档补丁，并通过新分支和 PR/MR 提交给团队审查，从而让 AI 辅助开发过程中的文档更新变得可追踪、可审查、可回滚、可维护。**

最终产品角色：

```text
对代码：观察者
对文档：补丁作者
对 Wiki：开发过程记录员
对 Git 平台：PR/MR 创建者
对团队：文档审查助手
```

最小闭环：

```text
代码变更
  → 影响分析
  → 生成补丁
  → 创建 PR/MR
  → 人工 review
  → 合并文档
  → 状态追踪
```

这比“就地自动修改文档”安全得多，也更符合真实团队的开发流程。

