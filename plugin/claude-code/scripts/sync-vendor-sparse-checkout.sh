#!/usr/bin/env bash
# Applies vendor-sparse-checkout.patterns to vendor/gentle-pi so the working
# tree only contains what user-prompt-submit.sh actually reads (currently:
# nothing under gentle-pi's content dirs — see HARNESS-AUDIT.md SS16; only
# root files like LICENSE/README stay, for provenance/license compliance).
# Run after any `git submodule update` or clone — sparse-checkout state lives
# in .git/ and is never committed by `git add vendor/gentle-pi`, so every
# clone (including CI) must reapply it.
set -euo pipefail

SCRIPTS_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPTS_DIR/../../.." && pwd)"
VENDOR_DIR="$REPO_ROOT/vendor/gentle-pi"
PATTERNS_FILE="$SCRIPTS_DIR/vendor-sparse-checkout.patterns"

if [ ! -d "$VENDOR_DIR/.git" ] && [ ! -f "$VENDOR_DIR/.git" ]; then
    echo "vendor/gentle-pi not initialized — run: git submodule update --init --recursive" >&2
    exit 1
fi

git -C "$VENDOR_DIR" sparse-checkout set --no-cone --stdin < "$PATTERNS_FILE"
