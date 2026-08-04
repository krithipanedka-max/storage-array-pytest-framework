#!/usr/bin/env sh
set -eu
python -m pytest --run-destructive -m destructive "$@"
