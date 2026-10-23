#!/usr/bin/env bash
# ============================================================
# Publica/atualiza o projeto em:
# https://github.com/denisvick-dev/cockpit-manager
#
# ANTES de rodar pela 1ª vez, crie o repositório VAZIO
# (sem README/gitignore) neste link já preenchido:
# https://github.com/new?name=cockpit-manager&description=Cockpit+Manager+em+Python+%2B+Streamlit+-+DB+F1+2026&visibility=public
# ============================================================
set -e
cd "$(dirname "$0")"
REPO_URL="https://github.com/denisvick-dev/cockpit-manager.git"

command -v git >/dev/null 2>&1 || { echo "[ERRO] Git não encontrado: https://git-scm.com/downloads"; exit 1; }

[ -d .git ] || git init -b main

git add -A
if ! git diff --cached --quiet; then
  git commit -m "Cockpit Manager Streamlit - DB F1 2026"
fi

git remote get-url origin >/dev/null 2>&1 \
  && git remote set-url origin "$REPO_URL" \
  || git remote add origin "$REPO_URL"

git branch -M main
echo "Enviando para o GitHub..."
git push -u origin main
echo "[OK] Publicado em https://github.com/denisvick-dev/cockpit-manager"
