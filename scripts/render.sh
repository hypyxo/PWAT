#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

FPS=30
DURATION=8

mkdir -p frames output

python3 -m venv .venv >/dev/null 2>&1 || true
# shellcheck disable=SC1091
source .venv/bin/activate

python -m pip install --upgrade pip >/dev/null
pip install -r scripts/requirements.txt >/dev/null

python scripts/generate_frames.py

ffmpeg -y \
  -framerate "${FPS}" \
  -i frames/frame_%04d.png \
  -t "${DURATION}" \
  -c:v libx264 \
  -pix_fmt yuv420p \
  -profile:v high \
  -level 4.1 \
  -movflags +faststart \
  output/kanban_warning.mp4
