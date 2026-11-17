#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
arquivo=${1:?Uso: bash scripts/restaurar.sh backups/arquivo.sql}
sha256sum -c "$arquivo.sha256"
inicio=$(date +%s)
# Cada restauração usa uma base nova; não apaga loja_cerrado.
alvo="loja_restore_$(date -u +%Y%m%d%H%M%S)_${RANDOM}"
bash scripts/mysql.sh -e "CREATE DATABASE ${alvo} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
bash scripts/mysql.sh "$alvo" < "$arquivo"
bash scripts/mysql.sh "$alvo" -e "SELECT COUNT(*) clientes FROM CLIENTE; SELECT COUNT(*) pedidos FROM PEDIDO; SELECT SUM(qtd*preco) total_itens FROM ITEM;"
printf 'Base: %s; tempo de restauração SQL: %ss\n' "$alvo" "$(( $(date +%s) - inicio ))"
printf 'Valide conteúdo e aplicação; esse tempo sozinho NÃO é o RTO completo.\n'
