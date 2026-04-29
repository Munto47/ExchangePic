#!/usr/bin/env bash
set -euo pipefail

branch="$(git branch --show-current)"

if [ -z "$branch" ]; then
  echo "No current branch. Refusing to push." >&2
  exit 1
fi

case "$branch" in
  main|master|develop|release|release/*|prod|production)
    echo "Refusing to push protected branch: $branch" >&2
    exit 1
    ;;
esac

git push -u origin "$branch"
