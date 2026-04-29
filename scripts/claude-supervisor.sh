#!/usr/bin/env bash
set -euo pipefail

HOURS="${1:-6}"
MAX_TURNS="${MAX_TURNS:-18}"
PERMISSION_MODE="${PERMISSION_MODE:-dontAsk}"
SLEEP_SECONDS="${SLEEP_SECONDS:-15}"

mkdir -p .claude/state .claude/logs

end_at=$(( $(date +%s) + HOURS * 3600 ))
cycle=0

TOOLS=(
  "Read"
  "Write"
  "Edit"
  "Grep"
  "Glob"
  "TodoWrite"
  "SlashCommand"

  "Bash(git status:*)"
  "Bash(git diff:*)"
  "Bash(git log:*)"
  "Bash(git rev-parse:*)"
  "Bash(git branch:*)"
  "Bash(git switch:*)"
  "Bash(git checkout:*)"
  "Bash(git add:*)"
  "Bash(git commit:*)"

  "Bash(gh auth status:*)"
  "Bash(gh pr view:*)"
  "Bash(gh pr create:*)"
  "Bash(gh pr edit:*)"

  "Bash(npm test:*)"
  "Bash(npm run:*)"
  "Bash(pnpm test:*)"
  "Bash(pnpm run:*)"
  "Bash(yarn test:*)"
  "Bash(yarn run:*)"
  "Bash(pytest:*)"
  "Bash(go test:*)"
  "Bash(cargo test:*)"
  "Bash(make test:*)"

  "Bash(./scripts/safe-git-push.sh:*)"
  "mcp__linear-server__*"
)

while [ "$(date +%s)" -lt "$end_at" ]; do
  cycle=$((cycle + 1))
  ts="$(date +%Y%m%d-%H%M%S)"
  log=".claude/logs/cycle-${cycle}-${ts}.jsonl"

  echo "== cycle ${cycle} started at ${ts} ==" | tee -a .claude/logs/supervisor.log

  if [ -f BLOCKED.md ]; then
    echo "BLOCKED.md exists. Stopping." | tee -a .claude/logs/supervisor.log
    exit 2
  fi

  set +e
  CLAUDE_LONGRUN=1 claude -p "/longrun

继续长期开发流程。只执行一个小而可验证的开发步骤。严格遵守 CLAUDE.md、.claude/state/ROADMAP.md 和 longrun skill。不要一次性做大任务。" \
    --output-format stream-json \
    --include-hook-events \
    --permission-mode "$PERMISSION_MODE" \
    --max-turns "$MAX_TURNS" \
    --allowedTools "${TOOLS[@]}" \
    2>&1 | tee "$log"

  status="${PIPESTATUS[0]}"
  set -e

  if [ "$status" -ne 0 ]; then
    echo "Claude exited with status ${status}. See ${log}" | tee -a .claude/logs/supervisor.log
    git status --short | tee -a .claude/logs/supervisor.log
    exit "$status"
  fi

  if [ -f BLOCKED.md ]; then
    echo "BLOCKED.md created. Stopping." | tee -a .claude/logs/supervisor.log
    exit 2
  fi

  dirty="$(git status --porcelain --untracked-files=normal | grep -vE '^(\?\? )?\.claude/state/' | grep -vE '^(\?\? )?\.claude/logs/' || true)"
  if [ -n "$dirty" ]; then
    echo "Dirty git state after cycle. Stopping for safety:" | tee -a .claude/logs/supervisor.log
    echo "$dirty" | tee -a .claude/logs/supervisor.log
    exit 3
  fi

  sleep "$SLEEP_SECONDS"
done

echo "Time budget reached. Supervisor stopped cleanly." | tee -a .claude/logs/supervisor.log
