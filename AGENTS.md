# Repository Guidelines

## Project Structure & Module Organization

DocGuard is split into a Python backend and a Vite/React frontend. Backend application code lives in `backend/app`: API routes are under `api/v1`, business logic under `services`, LLM adapters under `llm`, Git integrations under `git_providers`, database code under `database`, and Pydantic contracts under `schemas`. Backend tests belong in `backend/tests`.

Frontend code lives in `frontend/src`: shared API clients in `api`, reusable UI in `components`, hooks in `hooks`, route views in `pages`, shared types in `types`, and static assets in `assets`. `README.md` is the source of truth for the PR-first document governance model.

## Build, Test, and Development Commands

- `cd backend && uv sync`: install backend dependencies.
- `cd backend && uv run uvicorn app.main:app --reload`: run the FastAPI API on port `8000`.
- `cd backend && uv run --all-groups python -m pytest`: run backend tests.
- `cd backend && uv run ruff check app tests`: lint backend Python.
- `cd frontend && pnpm install`: install frontend dependencies.
- `cd frontend && pnpm dev`: run Vite on port `5173`; `/api` proxies to `localhost:8000`.
- `cd frontend && pnpm build`: type-check and build the frontend.
- `cd frontend && pnpm lint`: run ESLint.

## Coding Style & Naming Conventions

Use 4-space indentation, type hints, `snake_case` modules/functions, and `PascalCase` classes for Python. Prefer Pydantic models for contracts and keep route handlers thin by moving workflow logic into `services`.

Use TypeScript and React function components in the frontend. Name components and page files in `PascalCase`, hooks as `useSomething`, and API helpers with clear verb-based names. Keep styling consistent with the Tailwind CSS setup.

## Testing Guidelines

Backend tests use `pytest`; name files `test_*.py` and place them in `backend/tests`, mirroring the app area being tested. Add focused unit tests for services and regression tests for API behavior when changing routes. Frontend test tooling is not configured yet; if adding it, include scripts in `frontend/package.json`.

## Commit & Pull Request Guidelines

The current history uses short, imperative summaries such as `Init DocGuard: ...`. Keep commit subjects concise and describe one logical change. Pull requests should include purpose, main changes, test/lint results, linked issues if applicable, and screenshots for visible UI changes.

## Security & Configuration Tips

Backend settings load from `.env`; keep secrets such as `LLM_API_KEY`, provider tokens, and custom base URLs out of git. Do not commit generated folders or local runtime state such as `.venv`, `node_modules`, `dist`, `__pycache__`, or local SQLite databases.
