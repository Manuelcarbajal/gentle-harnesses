#!/usr/bin/env bash
set -euo pipefail

TESTS_DIR="$(cd "$(dirname "$0")" && pwd)"
LIBS_DIR="$TESTS_DIR/libs"

BATS_CORE_VERSION="v1.14.0"
BATS_ASSERT_VERSION="v2.1.0"
BATS_SUPPORT_VERSION="v0.3.0"

clone_or_update() {
    local name="$1" url="$2" tag="$3" dest="$LIBS_DIR/$name"
    if [ -d "$dest" ]; then
        printf 'already installed: %s\n' "$name"
        return
    fi
    printf 'installing %s %s...\n' "$name" "$tag"
    git clone --depth 1 --branch "$tag" "$url" "$dest" 2>/dev/null
}

mkdir -p "$LIBS_DIR"
clone_or_update bats-core    https://github.com/bats-core/bats-core    "$BATS_CORE_VERSION"
clone_or_update bats-assert  https://github.com/bats-core/bats-assert  "$BATS_ASSERT_VERSION"
clone_or_update bats-support https://github.com/bats-core/bats-support "$BATS_SUPPORT_VERSION"

printf 'done\n'
