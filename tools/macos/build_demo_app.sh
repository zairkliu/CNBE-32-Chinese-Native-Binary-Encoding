#!/usr/bin/env bash
set -euo pipefail

APP_NAME="${1:-CNBE32-Demo}"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

python3 -m pip install --upgrade pip
python3 -m pip install -e ".[demo]"

python3 -m PyInstaller \
  --noconfirm \
  --clean \
  --windowed \
  --name "$APP_NAME" \
  --collect-data cnbe32 \
  --add-data "src/cnbe32/data/cnbe32.db:cnbe32/data" \
  --hidden-import cnbe32_demo.app \
  --hidden-import cnbe32_demo.presenter \
  src/cnbe32_demo/app.py

echo "打包完成：dist/$APP_NAME.app"
