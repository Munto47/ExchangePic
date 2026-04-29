---
name: submit-pr
description: Finish a completed Linear issue by validating git state, committing remaining coherent changes, safely pushing the feature branch, creating or updating a GitHub PR, and writing the PR URL back to ROADMAP and Linear.
allowed-tools:
  - Read
  - Write
  - Edit
  - Grep
  - Glob
  - Bash(git status:*)
  - Bash(git diff:*)
  - Bash(git log:*)
  - Bash(git rev-parse:*)
  - Bash(git branch:*)
  - Bash(git add:*)
  - Bash(git commit:*)
  - Bash(./scripts/safe-git-push.sh:*)
  - Bash(gh pr view:*)
  - Bash(gh pr create:*)
  - Bash(gh pr edit:*)
  - mcp__linear-server__*
---

# Submit PR

Submit a PR only after acceptance criteria are satisfied.

## Required sequence

1. Read `CLAUDE.md`.
2. Read `.claude/state/ROADMAP.md`.
3. Confirm there is an active Linear issue and acceptance criteria are complete.
4. Run `git status` and inspect remaining changes.
5. If there are coherent uncommitted changes, commit them.
6. Refuse to continue if on main, master, develop, release, prod, or production.
7. Push using `./scripts/safe-git-push.sh`; do not run raw `git push`.
8. Check for existing PR with `gh pr view --json url`.
9. If no PR exists, create one with `gh pr create` using explicit title and body.
10. Record PR URL in `.claude/state/ROADMAP.md`.
11. Comment PR URL back to Linear.
12. Move Linear issue to In Review or Human Review if that status exists.
13. Never claim completion without the PR URL.

## PR body must include

- Linear issue URL or identifier
- Summary
- Tests run
- Risk / rollback notes
- Any follow-up work
