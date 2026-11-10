#!/bin/sh
# Validate the current native PCB designs without rewriting release packages.
set -eu
cd "$(dirname "$0")"
exec python3 build.py "$@"
