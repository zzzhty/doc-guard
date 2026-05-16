# DocWatcher Frontend

React + TypeScript + Vite frontend for DocWatcher.

## Commands

- `pnpm install`: install dependencies from `pnpm-lock.yaml`.
- `pnpm dev`: start Vite on port `5173`; `/api` proxies to the backend at `localhost:8000`.
- `pnpm build`: run TypeScript project build and produce `dist/`.
- `pnpm lint`: run ESLint.
- `pnpm preview`: preview the production build locally.

## Structure

- `src/api`: typed API clients.
- `src/hooks`: React Query hooks.
- `src/components`: reusable UI components.
- `src/pages`: route-level views.
- `src/types`: shared TypeScript types.
- `src/assets` and `public`: static assets.

The root `README.md` is the source of truth for product direction and MVP scope.
