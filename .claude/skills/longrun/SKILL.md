---
name: longrun
description: Run one recoverable long-running development worker iteration using Linear, ROADMAP state, git commits, tests, blockers, and PR handoff. Use when asked to continue the longrun development workflow.
allowed-tools:
  - Read
  - Write
  - Edit
  - Grep
  - Glob
  - TodoWrite
  - SlashCommand
  - Bash(git status:*)
  - Bash(git diff:*)
  - Bash(git log:*)
  - Bash(git rev-parse:*)
  - Bash(git branch:*)
  - Bash(git switch:*)
  - Bash(git checkout:*)
  - Bash(git add:*)
  - Bash(git commit:*)
  - Bash(npm test:*)
  - Bash(npm run:*)
  - Bash(pnpm test:*)
  - Bash(pnpm run:*)
  - Bash(yarn test:*)
  - Bash(yarn run:*)
  - Bash(pytest:*)
  - Bash(go test:*)
  - Bash(cargo test:*)
  - Bash(make test:*)
  - mcp__linear-server__*
---

# Longrun Worker Iteration

Perform exactly one small, recoverable development step.

## Required sequence

1. Read `CLAUDE.md`.
2. Read `.claude/state/ROADMAP.md`; create it if missing.
3. If `BLOCKED.md` exists, stop implementation and summarize the blocker.
4. Identify the active Linear issue from ROADMAP. If absent, use Linear MCP to find the next assigned issue that is ready to work.
5. Record the selected issue, goal, and acceptance criteria in `.claude/state/ROADMAP.md`.
6. Ensure work is on a non-protected feature branch.
7. Choose one small implementation step only.
8. Make code changes.
9. Run the narrowest useful validation first, then broader validation if appropriate.
10. If validation passes, commit coherent changes.
11. Update `.claude/state/ROADMAP.md` with:
    - completed step
    - commands run
    - results
    - next step
12. If all acceptance criteria are complete, invoke `/submit-pr`.
13. If blocked, write `BLOCKED.md`, update Linear with the blocker if possible, and stop.

## Completion rule

Never say the issue is complete unless a PR URL exists and is recorded in:
- `.claude/state/ROADMAP.md`
- Linear issue comment
