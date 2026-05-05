# 01. Engineering Baseline

## Goal

建立可验证的开发基线，让后续 milestone 的改动可以用稳定命令检查。完成后，后端 lint/test 可运行，前端 build/lint 保持通过，最小单元测试覆盖核心纯逻辑。

## Current State

- `frontend && pnpm build` 通过。
- `frontend && pnpm lint` 通过。
- `backend && uv run ruff check app tests` 已通过。
- 标准测试命令使用 `uv run --all-groups python -m pytest`，当前已有 15 个测试通过。
- `backend/tests` 已包含 15 个最小测试，后续仍需补服务层、provider 和 LLM fallback 覆盖。

## Deliverables

- 后端 ruff 清零，不引入行为变化。已完成。
- 明确后端依赖同步命令，并让 pytest 通过 `python -m pytest` 在当前 repo 中可执行。已完成。
- 新增最小 smoke/unit tests，覆盖不依赖外部服务的核心逻辑。已完成。
- 更新开发说明时只记录真实可运行命令，不写占位命令。已完成。

## Task Breakdown

### P0

- 清理 ruff 问题：移除未使用 import，处理 webhook 中未使用的 `payload`。已完成。
- 检查 `uv` dev dependency 安装方式；推荐目标命令为 `cd backend && uv sync --dev && uv run --all-groups python -m pytest`。已完成。
- 新增 `config_parser` 测试：解析 `project`、`docs`、`git.default_branch`、`modules`，验证空配置降级。已完成。
- 新增 `ModuleMatcher` 测试：验证 glob、`**` 前缀路径和无匹配场景。已完成。
- 新增 `doc_utils` 测试：验证 `extract_sections()`、`apply_patch_to_section()`、`generate_unified_diff()`。已完成。

### P1

- 新增 `ProjectService` local path 校验测试，使用临时 Git repo。
- 新增 FastAPI health smoke test，确认 app 可导入、`/health` 返回 ok。已完成。
- 在 README 或 `.codex` 文档中记录后端首次启动的依赖同步顺序。

## Interfaces

本 milestone 不新增业务 API。允许仅为测试调整 import、fixture 或纯函数边界。不要修改现有请求/响应 schema。

## Acceptance Criteria

- `cd backend && uv run ruff check app tests` 通过。
- `cd backend && uv run --all-groups python -m pytest` 通过，至少包含 8 个有效测试。
- `cd frontend && pnpm build` 继续通过。
- `cd frontend && pnpm lint` 继续通过。
- 后端测试不依赖真实 OpenAI、Gitea、GitLab、GitHub 服务。

## Risks

- 不要用 `ruff --fix` 做未审查的大范围改写。
- 不要为了让测试通过而跳过核心断言。
- 如果当前 `uv` 版本对 `--dev`/`--group dev` 行为不同，必须在文档中记录实际可运行命令。
