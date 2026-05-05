# 03. Impact Analysis Loop

## Goal

让用户对某个已扫描 commit 发起文档影响分析，并在 UI 中看到候选文档、影响等级、原因、置信度和状态操作。

## Current State

已完成。后端 impact analysis 会复用已有结果、使用 docops 候选文档、在缺少 docops 时执行路径相似度降级召回，并在无 LLM key 时生成保守 heuristic impact。前端 commit detail 已提供 Analyze Impact、impact 列表和 ignored/false_positive 状态操作。

## Deliverables

- commit detail 页面提供 “Analyze Impact” 按钮。已完成。
- 后端分析结果可重复查询，不重复创建同一 commit/document impact。已完成。
- 无 `docops.yml` 时提供文件名/路径相似度降级召回。已完成。
- impact 列表支持 ignore 和 false positive。已完成。
- LLM/API key 缺失、候选为空、调用失败都有明确 UI 状态。已完成。

## Task Breakdown

### P0

- 在 `ChangeDetail` 中调用 `POST /projects/{id}/changes/{commit_id}/analyze`。已完成。
- 前端新增 impact API/hook/types，显示 `document_path`、`module_name`、`impact_level`、`reason`、`confidence`、`status`。已完成。
- 后端 `ImpactService.analyze_commit()` 先检查已有 impacts；已有结果时返回已有记录。已完成。
- 增加降级候选召回：当 `docops.yml` 缺失或模块无匹配时，扫描 `docs/wiki` 中的 `.md/.yml/.yaml`，用 changed files 的目录名、文件名、模块词匹配候选文档。已完成。
- 分析失败时设置 `ScannedCommit.analysis_status = failed`，并返回可读错误。已完成。

### P1

- 增加 impact 状态更新按钮：`ignored`、`false_positive`。已完成。
- 按影响等级排序：high、medium、low，再按创建时间。已完成。
- 在 UI 中显示 “No affected docs found” 的空态，不把空结果当错误。已完成。
- 将 `ChangeInterpreter` 的 summary 保存到 commit 或单独字段，供详情页展示。后续优化项。

## Interfaces

- `GET /projects/{id}/impacts?status=` 保持列表接口。
- `PUT /projects/{id}/impacts/{impact_id}/status` 允许值限定为 `pending_analysis`、`ignored`、`false_positive`。
- `POST /projects/{id}/changes/{commit_id}/analyze` 返回 `DocImpactListResponse`；如果已分析，默认返回已有结果。
- `DocImpactResponse` 字段保持现有结构，不在本阶段引入 PR 字段之外的新必填字段。

## Acceptance Criteria

- 用户能从 commit detail 发起影响分析。
- 对有 `docops.yml` 的项目，changed files 可匹配到模块候选文档。
- 对无 `docops.yml` 的项目，仍能基于文档树做有限候选召回。
- 结果列表能解释每个文档为什么受影响。
- 用户可以把误报标记为 `false_positive` 或 `ignored`。

## Tests

- `ModuleMatcher` 与降级召回单元测试。
- `ImpactService` 测试使用 fake LLM，避免真实 OpenAI 调用。
- API 测试覆盖重复 analyze 不创建重复 impact。
- 前端 build/lint 通过。

## Risks

- 不要让 LLM 在没有候选文档时自由编造文档路径。
- 不要把测试文件变更默认判断为高风险，除非候选文档确实描述相关行为。
- LLM 错误必须落到 commit 状态和 API 响应，不能只记录日志。
