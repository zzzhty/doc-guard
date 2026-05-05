# 04. Patch Preview And Quality Gate

## Goal

让用户对单个 impact 生成章节级文档补丁，预览完整文件 diff，人工编辑并 approve/reject。完成后，只有 approved patch 可以进入创建 PR。

## Current State

已完成。`PatchService` 会把章节级结果合并回完整文档，章节未命中时追加 review section，缺少 LLM key 时生成保守人工 review patch。前端已提供 patch preview 页面，支持原文、补丁、diff、质量报告、Markdown 预览、编辑、approve/reject。

## Deliverables

- 修复 patch 合并语义：LLM 输出章节内容，后端合并回原始完整文档。已完成。
- Patch 预览页显示原文、patched content、unified diff、quality report。已完成。
- 用户可以编辑 patched content，重新生成 diff。已完成。
- 用户可以 approve/reject；未 approve 不能创建 PR。已完成。
- quality gate 对低分或 error 级问题给出阻断或强 review 标记。已完成。

## Task Breakdown

### P0

- 修改 `PatchService.generate_patch()`：对 `update_section` 使用 `apply_patch_to_section(original_content, target_section_heading, new_content)` 生成完整 `patched_content`。已完成。
- 如果 `target_section_heading` 未命中，默认改为 `append_section`，不允许覆盖整篇。已完成。
- 为 `append_section` 定义最小规则：追加到文档末尾，标题由 LLM 返回或使用 `## DocGuard Review Required`。已完成。
- 为 `create_wiki_note` 定义最小规则：生成新 wiki 文件路径，但本阶段先只允许预览，不直接写入。后续优化项。
- 前端新增 patch API/hook/types，支持 generate、get、update、approve、reject。已完成。
- 新增 patch preview 页面，入口来自 impact list。已完成。

### P1

- 在 preview 页面加入简单 Markdown 预览。已完成。
- 质量报告以结构化 JSON 展示 issues、score、requires_review。已完成。
- 对 `review.requires_review = true` 的 patch 显示强 review 提示，但仍允许 approve；创建 PR 时写入 PR review notes。已完成。
- 支持 `mark_stale`：给文档添加可 review 的过期标记。已完成。

## Interfaces

- `POST /projects/{id}/impacts/{impact_id}/patches?change_type=update_section` 返回 `Patch` 摘要。
- `GET /patches/{patch_id}` 返回 `original_content`、`patched_content`、`diff`、`quality_report`、`status`。
- `PUT /patches/{patch_id}` 接收完整 `patched_content`，后端重新计算 diff。
- `POST /patches/{patch_id}/approve` 仅允许从 `pending` 或 `edited` 到 `approved`。
- `POST /patches/{patch_id}/reject` 设置 `rejected`，并保留历史记录。

## Acceptance Criteria

- 生成 patch 后，`patched_content` 是完整文档，不是章节片段。
- 原文和补丁 diff 能在 UI 中同时查看。
- 编辑 patched content 后 diff 更新。
- 只有 `approved` patch 能进入 PR 创建。
- 当章节未命中时，系统不会覆盖原文件。

## Tests

- `PatchService` 使用 fake LLM 测试命中章节、未命中章节、append section。
- `doc_utils.apply_patch_to_section()` 覆盖多级 heading。
- API 测试覆盖 approve/reject/status。
- 前端 build/lint 通过。

## Risks

- 不要把 LLM 生成内容直接信任为完整文件。
- 不要把 quality report 只存字符串后前端无法解析；如果暂存 JSON 字符串，前端必须安全 parse。
- 不要允许 rejected patch 被创建 PR。
