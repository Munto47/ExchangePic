#!/usr/bin/env bash
set -euo pipefail

echo "== commands =="
for cmd in git gh jq tmux claude rg; do
  command -v "$cmd" >/dev/null
  echo "ok: $cmd -> $(command -v "$cmd")"
done

echo
echo "== git =="
git rev-parse --is-inside-work-tree
git remote -v
git status --short

echo
echo "== gh =="
gh auth status --active

echo
echo "== claude =="
claude --version

echo
echo "== deepseek env =="
test "${ANTHROPIC_BASE_URL:-}" = "https://api.deepseek.com/anthropic"
test -n "${ANTHROPIC_AUTH_TOKEN:-}"
echo "ok: DeepSeek env present"

echo
echo "== mcp =="
claude mcp list || true

echo
echo "== smoke test =="
claude -p "只回答 OK" --output-format json --max-turns 1

echo
echo "healthcheck passed"
