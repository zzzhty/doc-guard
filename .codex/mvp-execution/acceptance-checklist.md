# MVP Acceptance Checklist

本清单对照 `README.md` 中的 MVP workflow 和验收目标。每完成一个 milestone 后更新状态。

| # | 验收标准 | 目标 Milestone | 当前状态 | 验证方式 |
| --- | --- | --- | --- | --- |
| 1 | 可以接入一个真实 Git 项目 | M1 | 未完成 | UI 创建 local 项目，后端保存 Project，显示 docops 状态 |
| 2 | 可以读取目标项目的代码和文档 | M1 | 未完成 | 打开文档树和文档内容；commit diff 可查看 |
| 3 | 可以扫描某个代码 commit | M1 | 部分完成 | UI 扫描 commit，返回 commit metadata、changed files、diff |
| 4 | 可以判断受影响文档 | M2 | 部分完成 | 点击 Analyze，生成 DocImpact 列表 |
| 5 | 可以生成章节级文档补丁 | M3 | 部分完成 | 对 impact 生成 patch，patched content 是完整文档 |
| 6 | 可以创建 docguard/* 分支 | M4 | 部分完成 | Gitea 中出现 docguard 分支 |
| 7 | 可以提交 docs/wiki 修改 | M4 | 部分完成 | Gitea 分支 commit 只包含 docs/wiki/meta 允许路径 |
| 8 | 可以创建 PR/MR | M4 | 未完成 | Gitea 中出现真实 PR，DB 保存 pr_number/pr_url |
| 9 | PR 描述能说明来源 commit、影响文档和需确认事项 | M4 | 部分完成 | PR body 包含 source change、affected docs、review notes、quality checks |
| 10 | PR 合并后，平台状态能更新 | M5 | 未完成 | 合并或刷新 PR 后 impact 变为 pr_merged，Dashboard 计数更新 |

## Milestone Completion Gates

### M0 Engineering Baseline

- [x] `cd backend && uv run ruff check app tests` 通过。
- [x] `cd backend && uv run --all-groups python -m pytest` 通过。
- [x] `cd frontend && pnpm build` 通过。
- [x] `cd frontend && pnpm lint` 通过。

### M1 Local Readonly Loop

- [ ] 项目接入保存 `config_yaml` 或明确 missing。
- [ ] commit 扫描保存 changed files。
- [ ] 前端能查看文档树、文档内容、commit detail。
- [ ] 本阶段不写目标 repo 文件。

### M2 Impact Analysis Loop

- [ ] commit detail 可触发 impact analysis。
- [ ] 有 docops 时按模块匹配候选文档。
- [ ] 无 docops 时有降级召回。
- [ ] 用户可标记 ignored/false_positive。

### M3 Patch Preview And Quality Gate

- [ ] Patch 合并回完整文档。
- [ ] UI 显示原文、补丁、diff、质量报告。
- [ ] 用户可编辑、approve、reject。
- [ ] rejected 或未 approved patch 不能创建 PR。

### M4 Gitea PR-First Loop

- [ ] Gitea provider 接入 `ProjectService`。
- [ ] 创建 `docguard/*` 分支。
- [ ] 提交 approved patches。
- [ ] 创建真实 Gitea PR。
- [ ] 保存 PR number、URL、body、items。

### M5 Dashboard And Close Loop

- [ ] Dashboard 使用真实 API 数据。
- [ ] Doc PR 管理页可刷新状态。
- [ ] merged PR 更新 impacts 为 `pr_merged`。
- [ ] closed PR 更新 impacts 为 `pr_rejected`。
- [ ] `README.md` 中的 MVP 验收目标全部可演示。
