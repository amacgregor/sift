#!/usr/bin/env bash
# Zero-key ablation: structural heuristic vs domain checklist.
set -euo pipefail
cd "$(dirname "$0")/.."
python -m sift.cli compare --suts heuristic,checklist --out results/compare
cp results/compare/comparison.md results/examples/comparison.md
cp results/compare/heuristic/report.md results/examples/report.md
