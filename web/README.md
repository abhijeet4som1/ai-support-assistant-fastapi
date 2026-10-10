# web – React application

Vite 7 · React 19 · TypeScript (strict) · TanStack Router (file-based) · TanStack Query ·
Tailwind CSS v4 · Lingui (i18n) · Vitest + Testing Library.

## Layout

```
src/
├── main.tsx                 bootstrap: i18n → QueryClient → Router
├── routes/                  file-based routes (TanStack Router generates routeTree.gen.ts)
│   ├── __root.tsx           app shell: header, nav, error/not-found components
│   ├── login.tsx            /login (?next=)
│   ├── _authenticated.tsx   guard layout (redirects to /login)
│   └── _authenticated/
│       ├── chat.tsx                 /chat?companyId&conversationId
│       ├── history/index.tsx        /history?companyId&coverage
│       ├── history/$conversationId  conversation detail + why-this-answer
│       └── companies/{index,new,$companyId}.tsx
├── components/
│   ├── ui/                  design-system primitives (Button, Input, Dialog, Badge, Progress, Table, ...)
│   ├── chat/                company picker, conversation list, thread, assistant card, composer
│   ├── companies/           list, form, guideline status badge
│   ├── guidelines/          upload (with conflict dialog), progress, version history, viewer
│   ├── feedback/            thumbs + correction dialog, corrections list
│   ├── history/             filters, table, why-this-answer panel
│   ├── errors/              route/app error views, not found, pending
│   └── layout/              header, network banner
├── api/                     schema.d.ts (generated), openapi-fetch client, query hooks, error mapper
├── lib/                     cn() and small utilities
├── styles/theme.css         Tailwind v4 import + design tokens (@theme)
├── locales/{en,de}/messages.po   translation catalogs (source of truth, imported directly)
├── i18n.ts                  locale detection and activation
└── test/setup.ts            jest-dom matchers, i18n activation for tests
```

## Design system rules

These are enforced by ESLint (`@app/eslint-config/react`):

- **No inline styles.** The `style` prop is forbidden. The single dynamic value in the app
  (ingestion progress) uses the native `<progress>` element.
- **Static class names only.** No template-literal `className`; compose with `cn()` and declare
  variants with `class-variance-authority`. Tailwind can only see complete class strings.
- **Semantic tokens only.** Use `bg-primary`, `text-muted-foreground`, `border-border` … defined
  in `styles/theme.css`; never raw palette classes like `bg-indigo-600`.
- Accessible primitives come from Radix UI; components live in the repo (shadcn-style), so they
  can be changed freely.

## Internationalisation

Lingui with `.po` catalogs, no compile step: `@lingui/vite-plugin` compiles catalogs on import.

```sh
pnpm lingui:extract     # scan <Trans>/t`` usages and update src/locales/*/messages.po
```

Translate the `msgstr` entries in `src/locales/de/messages.po` and reload. The UI chrome is
translated; assistant answers follow the customer's language.

## API access

`src/api/schema.d.ts` is generated from the OpenAPI document (`pnpm api:types`, see
`scripts/gen-api-types.mjs`, which types binary payloads as `Blob`), which is itself generated from
the Smithy model. `src/api/client.ts` builds an openapi-fetch client on it (same
origin, bearer token added by middleware, every non-2xx response thrown as `ApiError` carrying the
modelled error name from `X-Amzn-Errortype`) and `$api` from openapi-react-query for typed
`queryOptions`/hooks. `src/api/errors.ts` maps `ApiError` to UI behaviour (field errors on forms,
redirect on 401, route error components, retry banners).

## Scripts

```sh
pnpm dev               # vite on :5173 (in Docker it is proxied by nginx)
pnpm build             # routes:generate → tsc → vite build (dist/)
pnpm test              # vitest run
pnpm lint | pnpm typecheck | pnpm routes:generate
```

## Error handling

## Authentication and client state

Client state is Jotai on one shared store (`src/state/store.ts`) so router guards and fetch
middleware can read it outside React; server state stays in TanStack Query.

- `src/auth/atoms.ts`: `tokensAtom` (access + refresh token, persisted in localStorage; an
  `idToken` slot is reserved for a future OpenID Connect provider), `userAtom` (memory only),
  derived `isAuthenticatedAtom` (refresh token still valid) and `accessTokenStaleAtom`.
- `src/routes/_authenticated.tsx` is the only guard: no session → redirect to `/login?next=`;
  otherwise it loads `/api/auth/me` once, writes `userAtom`, and renders children after that.
  Everything else only reads the atoms.
- `src/api/client.ts` middleware: refreshes the access token before use when it is about to
  expire, and on a 401 refreshes once (single-flight across concurrent requests) and replays the
  request. A rejected refresh clears the session, which makes the guard redirect.
- Logout calls `/api/auth/logout` to revoke the refresh-token family, then clears the store.

- Root `ErrorBoundary` → full-page fallback with request id, reload / home.
- Route-level `errorComponent` / `notFoundComponent` / `pendingComponent`.
- Forms: zod validation first, server `ValidationException.fieldList` mapped onto fields.
- Chat: a failed assistant turn renders inline with a retry action.
- Network failure: persistent banner with automatic retry of idempotent queries only.
