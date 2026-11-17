#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [ ! -f .env ]; then
  umask 077
  python3 - <<'CODE'
import secrets
from pathlib import Path
Path('.env').write_text(''.join(f'{nome}={secrets.token_hex(24)}\n' for nome in
    ['TOKEN_ANA','TOKEN_BRUNO','TOKEN_GESTOR','TOKEN_SERVICO']))
CODE
fi
mkdir -p evidencias backups
docker version >/dev/null
docker compose version
printf 'Preparação concluída. Execute: docker compose up -d --build --wait\n'
