# @app/tsconfig

Shared TypeScript configuration bases for the workspace.

| File         | Use in                                  |
| ------------ | --------------------------------------- |
| `base.json`  | strictness + module hygiene, everything |
| `node.json`  | `api` (NodeNext, ES2023 lib)            |
| `react.json` | `web` (bundler resolution, DOM lib)     |

Extend with `"extends": "@app/tsconfig/node.json"`.
