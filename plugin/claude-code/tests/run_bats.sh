#!/usr/bin/env bash
TESTS_DIR="$(cd "$(dirname "$0")" && pwd)"
export PATH="$HOME/.local/bin:$PATH"
exec "$TESTS_DIR/libs/bats-core/bin/bats" --recursive "$TESTS_DIR/bats" "$@"
