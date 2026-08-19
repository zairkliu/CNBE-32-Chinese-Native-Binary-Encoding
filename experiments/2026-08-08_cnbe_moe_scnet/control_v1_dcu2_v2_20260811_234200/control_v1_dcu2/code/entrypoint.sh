#!/usr/bin/env bash
set -e

if [ $# -eq 0 ]; then
  echo "Usage: docker run IMAGE [command]"
  echo "Example: python scripts/train_scnet.py --smoke"
  exit 1
fi

exec "$@"
