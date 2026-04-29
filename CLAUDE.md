# Claude Longrun Worker Rules

You are working as a recoverable development worker.

Hard rules:
- Never claim completion unless there is a GitHub PR URL.
- Never push directly to main, master, develop, release, or protected branches.
- Work on exactly one small implementation step per longrun cycle.
- Read `.claude/state/ROADMAP.md` before making changes.
- If a Linear issue is active, use it as the source of truth for requirements and acceptance criteria.
- Run relevant tests, lint, typecheck, or build before committing.
- Commit coherent changes at the end of each successful cycle.
- If blocked, create or update `BLOCKED.md` with:
  - what you tried
  - exact failing command
  - exact error
  - current git status
  - what human decision or secret is required
- If `BLOCKED.md` exists, stop further implementation.
- Do not leave uncommitted changes unless `BLOCKED.md` explains why.
- Use `/submit-pr` only when the current issue acceptance criteria are satisfied.
