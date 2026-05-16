# DocWatcher MVP Execution Pack

本目录把 `README.md` 中的产品 guide 和当前进度转成可执行工程计划。执行主线固定为 **Local -> Gitea**：先补齐本地只读闭环和补丁安全性，再接真实 Gitea PR。

## 文档索引

| 文件 | 用途 |
| --- | --- |
| `00-scope-and-decisions.md` | MVP 范围、默认决策、非目标和状态主线 |
| `01-engineering-baseline.md` | Milestone 0：工程基线、lint、test 和最小测试 |
| `02-local-readonly-loop.md` | Milestone 1：本地项目接入、docops、文档树、commit detail |
| `03-impact-analysis-loop.md` | Milestone 2：文档影响分析和状态流转 |
| `04-patch-preview-quality-gate.md` | Milestone 3：章节级补丁、预览、编辑和质量门禁 |
| `05-gitea-pr-first-loop.md` | Milestone 4：Gitea provider、分支、commit、真实 PR |
| `06-dashboard-close-loop.md` | Milestone 5：看板、PR 管理和状态回流 |
| `acceptance-checklist.md` | 对照 `README.md` 中 MVP workflow 的验收清单 |

## 执行顺序

1. 先完成 `01-engineering-baseline.md`，保证后端 lint/test 命令可运行。
2. 完成 `02-local-readonly-loop.md`，让用户能接入本地 Git 项目、读取 `docops.yml`、浏览文档和查看 commit diff。
3. 完成 `03-impact-analysis-loop.md`，让扫描 commit 可以产生可解释的文档影响结果。
4. 完成 `04-patch-preview-quality-gate.md`，修复 patch 覆盖风险，并提供人工预览/编辑/审批。
5. 完成 `05-gitea-pr-first-loop.md`，创建真实 `doc-watcher/*` 分支和 Gitea PR。
6. 完成 `06-dashboard-close-loop.md`，把 PR 状态回流到文档债务看板。

## 全局执行约束

- MVP 只做“已合并 commit -> 文档 PR”，不做开放 PR/MR companion flow。
- MVP provider 只覆盖 `local` 和 `gitea`；GitLab/GitHub 保留接口，不进入本轮实现。
- 正式文档和 wiki 默认都走 PR，不直接写主分支。
- LLM 只生成候选变更，所有写入必须进入可 review 的分支/PR。
- Patch 写入必须是完整文档结果，禁止把章节片段直接覆盖整个文件。
- 每个 milestone 完成后更新 `acceptance-checklist.md` 对应项。

## 完成定义

每个 milestone 必须同时满足：

- 后端和前端命令按文档要求通过，或记录明确阻塞原因。
- 新增 API/schema 有前端调用或测试覆盖，不保留孤立接口。
- UI 能从上一阶段自然进入下一阶段，不依赖手工调用 API。
- 失败状态对用户可见，不只写入服务端日志。
