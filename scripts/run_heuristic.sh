#!/usr/bin/env bash
# Review HEAD against its parent. Pass a path to review a patch file instead.
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ "${1:-}" != "" ]]; then
  python -m sift.cli review --diff "$1"
else
  git diff HEAD~1 | python -m sift.cli review
fi
