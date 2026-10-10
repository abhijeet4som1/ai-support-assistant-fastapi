# @app/eslint-config

Shared ESLint 9 flat configs.

- `@app/eslint-config/base` – TypeScript (type-checked), import ordering, Prettier compatibility.
- `@app/eslint-config/node` – base + Node globals (used by `api`).
- `@app/eslint-config/react` – base + React, hooks, a11y, plus the design-system rules:
  - `style` prop is forbidden (no inline styles),
  - `className={\`...\`}`template literals are forbidden (static classes only, compose with`cn()`/`cva`).
