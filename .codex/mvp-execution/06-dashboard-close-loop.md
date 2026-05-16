# 06. Dashboard And Close Loop

## Goal

让用户能在看板中看到文档债务和 DocWatcher PR 状态，并在 PR 合并或关闭后同步更新 impact 状态，形成 MVP 闭环。

## Current State

已完成。后端 `/dashboard/projects/{project_id}` 返回真实统计和最近 impact 活动；Doc PR list/get/refresh/close 路由已接入状态同步；前端 Dashboard 不再使用占位数据，并新增项目内 Doc PR 管理页；Gitea pull_request webhook 会按 `doc-watcher/*` 分支回写 merged/closed/open 状态。

## Deliverables

- [x] Dashboard 展示真实项目统计：待分析、已生成 patch、PR open/merged/rejected、高风险文档。
- [x] Doc PR 管理页展示所有 DocWatcher PR，支持刷新状态和打开外部 PR URL。
- [x] `refresh-status` 查询 provider 的真实 PR 状态。
- [x] Gitea webhook 接收到 DocWatcher PR 合并/关闭事件时更新 `DocPR`、`DocPRItem`、`DocImpact`。
- [x] `acceptance-checklist.md` 的 10 条 MVP 验收项全部可验证。

## Task Breakdown

### P0

- [x] 前端 Dashboard 接入真实 API；如果没有项目，显示连接项目入口。
- [x] 新增项目内 Doc PR 列表页，显示 title、source commit、branch、status、created_at、pr_url。
- [x] `DocPRService.refresh_status()` 对 Gitea 调用 `get_pr()`，映射 `open`、`merged`、`closed`。
- [x] 状态映射规则：merged -> impact `pr_merged`；closed without merged -> impact `pr_rejected`；open -> 保持 `pr_created`。
- [x] `close_pr()` 对 Gitea 调用 provider close；local provider 仅更新 DB 并标记为 local-only。

### Post-MVP Hardening

- 加强 Gitea webhook 事件签名、来源和仓库匹配校验。
- Dashboard 增加更完整的最近活动流：patch approved、PR created、PR merged。
- 增加过滤器：impact level、status、module。

## Interfaces

- `GET /dashboard/projects/{project_id}` 返回真实 `stats` 和 `recent_activity`。
- `POST /doc-prs/{doc_pr_id}/refresh` 返回最新 `status`、`pr_url`、`merged_at`。
- `POST /webhooks/gitea` 处理 PR 事件，成功返回 `{ "status": "received" }`。
- 前端 PR 状态颜色固定：open=blue，merged=green，closed/rejected=red，needs_update/conflict=amber。

## Acceptance Criteria

- [x] 创建 PR 后，Dashboard 的 open PR 数量增加。
- [x] Gitea PR 合并后，刷新状态会把 DocPR 标记为 merged，把相关 impacts 标记为 `pr_merged`。
- [x] Gitea PR 关闭后，相关 impacts 标记为 `pr_rejected`。
- [x] 用户可以从 Doc PR 管理页打开真实 PR URL。
- [x] Dashboard 不再显示占位 `—` 数据。

## Tests

- [x] `DocPRService.refresh_status()` 使用 fake provider 测试 open/merged/closed 映射。
- [x] Dashboard API 测试覆盖各 impact/PR 状态计数。
- [x] Webhook handler 测试覆盖 Gitea pull_request merged。
- [x] 前端 build/lint 通过。

## Risks

- Webhook 不能盲目信任任意 payload；MVP 至少校验项目 provider/repository/branch 前缀。
- 状态回流必须幂等，重复 webhook 或 refresh 不能重复修改无关记录。
- PR closed 不一定等于 rejected；需要用 merged_at 或 provider merged 字段区分。
