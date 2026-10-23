@echo off
REM ============================================================
REM  Publica/atualiza o projeto em:
REM  https://github.com/denisvick-dev/cockpit-manager
REM
REM  ANTES de rodar pela 1a vez, crie o repositorio VAZIO
REM  (sem README/gitignore) neste link ja preenchido:
REM  https://github.com/new?name=cockpit-manager&description=Cockpit+Manager+em+Python+%2B+Streamlit+-+DB+F1+2026&visibility=public
REM ============================================================
chcp 65001 >nul
cd /d %~dp0
set REPO_URL=https://github.com/denisvick-dev/cockpit-manager.git

where git >nul 2>nul
if errorlevel 1 (
  echo [ERRO] Git nao encontrado. Instale em https://git-scm.com/download/win e rode de novo.
  pause
  exit /b 1
)

if not exist .git (
  echo Inicializando repositorio local...
  git init -b main
)

git add -A
git commit -m "Cockpit Manager Streamlit - DB F1 2026" >nul 2>&1

git remote get-url origin >nul 2>&1
if errorlevel 1 (
  git remote add origin %REPO_URL%
) else (
  git remote set-url origin %REPO_URL%
)

git branch -M main
echo Enviando para o GitHub (faca login na janela que abrir)...
git push -u origin main

if errorlevel 1 (
  echo.
  echo [ERRO] O push falhou. Confira se o repositorio vazio
  echo "cockpit-manager" ja foi criado em github.com/denisvick-dev
  echo e se voce fez login com a conta certa.
) else (
  echo.
  echo [OK] Publicado em https://github.com/denisvick-dev/cockpit-manager
)
pause
