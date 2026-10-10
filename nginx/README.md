# nginx – reverse proxy and static hosting

nginx is the single entry point of the local stack: it gives the app a hostname
(`http://assistant.localhost`), serves the built web app, and proxies the API so
browser and API share one origin (no CORS).

## Routing

| Path                  | Production (`docker-compose.yml`)          | Development (`docker-compose.dev.yml`)    |
| --------------------- | ------------------------------------------ | ----------------------------------------- |
| `/api/conversations*` | → `api:3000`, read timeout **120 s** (LLM) | same                                      |
| `/api/*`              | → `api:3000`, read timeout 60 s            | same                                      |
| `/assets/*`           | static, `Cache-Control: immutable`         | → `web:5173` (vite)                       |
| `/*`                  | static SPA fallback to `index.html`        | → `web:5173` with websocket upgrade (HMR) |

nginx mints an `X-Request-Id` (`$request_id`) for every request and forwards it to the api,
which uses it as its log request id and echoes it back on every response. Client-supplied
ids are deliberately not trusted.

## Files

- `templates/default.conf.template` – production server block. The nginx image renders
  templates with `envsubst` at start-up; only `APP_*` variables are substituted
  (`NGINX_ENVSUBST_FILTER=^APP_`), so nginx's own `$uri`, `$host` are untouched.
- `templates-dev/default.conf.template` – development server block.
- `proxy.conf` – shared proxy headers/timeouts.

Images are built from the root `Dockerfile` (`nginx` and `nginx-dev` targets).

## Hostname and port

- `APP_HOST` (default `assistant.localhost`). Browsers resolve any `*.localhost` name to
  loopback without configuration. For `curl` and other tools add
  `127.0.0.1 assistant.localhost` to `/etc/hosts`, or use `http://localhost`, which is
  also accepted.
- `NGINX_PORT` (default `80`). Set e.g. `NGINX_PORT=8080` in `.env` if 80 is taken, then
  browse `http://assistant.localhost:8080`.

## Changing the hostname

Set `APP_HOST=myname.localhost` in `.env` and restart; the template picks it up.

The templates resolve the `api` (and, in dev, `web`) service names through Docker's embedded DNS at
request time (`resolver 127.0.0.11 valid=10s` with a variable `proxy_pass`) rather than a static
`upstream` block, so recreating the api container, for example after changing `.env`, does not
leave nginx pointing at a stale address. Vite's
`server.allowedHosts` in `web/vite.config.ts` must include the new name for dev mode.

## HTTPS (optional)

```sh
./scripts/tls/setup.sh                                   # mkcert: local CA + certificate for assistant.localhost
docker compose -f docker-compose.yml -f docker-compose.tls.yml up -d --build
```

`templates-tls/` serves HTTPS on 443 with the mkcert certificate and redirects HTTP to HTTPS.
Certificates live in `nginx/certs/` (git-ignored). Requires [mkcert](https://github.com/FiloSottile/mkcert).
