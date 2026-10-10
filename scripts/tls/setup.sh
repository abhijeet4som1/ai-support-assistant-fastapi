#!/usr/bin/env sh
# Generates a locally-trusted certificate for assistant.localhost with mkcert and installs the
# local CA in your trust store (one-time). Then start with:
#   docker compose -f docker-compose.yml -f docker-compose.tls.yml up -d --build
set -eu
cd "$(dirname "$0")/../.."
HOST="${APP_HOST:-assistant.localhost}"
if ! command -v mkcert >/dev/null 2>&1; then
  echo "mkcert is not installed. macOS: brew install mkcert nss   Linux: see https://github.com/FiloSottile/mkcert#installation" >&2
  exit 1
fi
mkcert -install
mkdir -p nginx/certs
mkcert -cert-file nginx/certs/server.pem -key-file nginx/certs/server-key.pem "$HOST" localhost 127.0.0.1 ::1
echo "Certificates written to nginx/certs/ (git-ignored). Start with:"
echo "  docker compose -f docker-compose.yml -f docker-compose.tls.yml up -d --build"
