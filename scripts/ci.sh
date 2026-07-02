#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"

echo "==> Checking committed whitespace"
git show --check --pretty=format: HEAD

echo "==> Checking working-tree whitespace"
git diff --check

echo "==> Checking staged whitespace"
git diff --cached --check

echo "==> Checking Markdown links"
python3 scripts/check_markdown_links.py

echo "==> Installing frontend dependencies"
npm ci

echo "==> Linting frontend"
npm run lint

echo "==> Type-checking frontend"
npm run typecheck

echo "==> Building frontend"
npm run build

echo "==> Testing frontend"
npm test

echo "==> Preparing backend environment"
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e "apps/api[dev]"

echo "==> Linting backend"
ruff check apps/api

echo "==> Type-checking backend"
mypy apps/api/src

echo "==> Testing backend"
pytest apps/api/tests
