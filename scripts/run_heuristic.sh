#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python -m sift.cli run --sut heuristic --out results/latest
