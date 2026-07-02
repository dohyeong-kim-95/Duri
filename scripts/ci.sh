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
