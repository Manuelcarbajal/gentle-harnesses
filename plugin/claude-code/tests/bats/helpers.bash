#!/usr/bin/env bash
# helpers.bash — loaded by every bats test file

BATS_LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../libs" && pwd)"
load "$BATS_LIB_DIR/bats-support/load"
load "$BATS_LIB_DIR/bats-assert/load"

SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../scripts" && pwd)"

setup() {
    STUB_DIR="$(mktemp -d)"
    export STUB_DIR

    # Use a controlled minimal PATH so real gentle-ai/codegraph are not found
    # unless a stub is explicitly created.  jq lives at ~/.local/bin which is
    # always prepended; standard POSIX tools come from /usr/bin and /bin.
    export PATH="$HOME/.local/bin:$STUB_DIR:/usr/bin:/bin:/usr/local/bin"

    # On Windows/Git Bash, git.exe lives here — needed for passthrough in stubs
    if [ -d "/c/Program Files/Git/bin" ]; then
        export PATH="$PATH:/c/Program Files/Git/bin"
    fi

    # Python3 shim: always create one in STUB_DIR so post-compaction tests work.
    # Find the real python3/python executable to delegate to.
    _real_python3=""
    for _candidate in \
        "/c/Users/manue/AppData/Local/Programs/Python/Python311/python.exe" \
        "/c/Users/manue/AppData/Local/Programs/Python/Python311/python3.exe" \
        "/c/Users/manue/AppData/Local/Microsoft/WindowsApps/python3.exe" \
        "/usr/bin/python3" \
        "/usr/local/bin/python3"; do
        if [ -x "$_candidate" ]; then
            _real_python3="$_candidate"
            break
        fi
    done
    if [ -n "$_real_python3" ]; then
        printf '#!/usr/bin/env bash\nexec "%s" "$@"\n' "$_real_python3" > "$STUB_DIR/python3"
        chmod +x "$STUB_DIR/python3"
    fi

    # Use a per-test project dir so tests don't pollute each other
    TEST_PROJECT_DIR="$(mktemp -d)"
    export CLAUDE_PROJECT_DIR="$TEST_PROJECT_DIR"

    # Clear all stub env vars
    unset STUB_GENTLE_AI_VERSION
    unset STUB_GENTLE_AI_DOCTOR_EXIT
    unset STUB_GENTLE_AI_VALIDATE_EXIT
    unset STUB_GENTLE_AI_REVIEW_STATUS
    unset STUB_GENTLE_AI_STATUS_EXIT
    unset STUB_GIT_SHORTSTAT
    unset STUB_GIT_NAMES
    unset STUB_PYTHON3_TRIGGER
    unset CLAUDE_TOOL_NAME
    unset CLAUDE_TOOL_INPUT
    unset CLAUDE_PLUGIN_ROOT
}

teardown() {
    rm -rf "$STUB_DIR"
    rm -rf "$TEST_PROJECT_DIR"
}

create_stub_gentle_ai() {
    cat > "$STUB_DIR/gentle-ai" << 'STUB_EOF'
#!/usr/bin/env bash
DOCTOR_EXIT="${STUB_GENTLE_AI_DOCTOR_EXIT:-0}"
VALIDATE_EXIT="${STUB_GENTLE_AI_VALIDATE_EXIT:-0}"
STATUS_EXIT="${STUB_GENTLE_AI_STATUS_EXIT:-0}"

# VERSION: use set-check so empty string means "output nothing and fail"
if [ "${STUB_GENTLE_AI_VERSION+isset}" = "isset" ]; then
    VERSION="$STUB_GENTLE_AI_VERSION"
else
    VERSION="gentle-ai 1.0.0"
fi

REVIEW_STATUS="${STUB_GENTLE_AI_REVIEW_STATUS:-}"

case "$1" in
    --version)
        if [ -n "$VERSION" ]; then
            echo "$VERSION"
            exit 0
        else
            exit 1
        fi
        ;;
    doctor)
        exit "$DOCTOR_EXIT"
        ;;
    review)
        case "$2" in
            validate)
                exit "$VALIDATE_EXIT"
                ;;
            status)
                if [ -n "$REVIEW_STATUS" ]; then
                    echo "$REVIEW_STATUS"
                fi
                exit "$STATUS_EXIT"
                ;;
        esac
        ;;
esac
exit 0
STUB_EOF
    chmod +x "$STUB_DIR/gentle-ai"
}

create_stub_codegraph() {
    cat > "$STUB_DIR/codegraph" << 'STUB_EOF'
#!/usr/bin/env bash
exit 0
STUB_EOF
    chmod +x "$STUB_DIR/codegraph"
}

create_stub_git() {
    cat > "$STUB_DIR/git" << 'STUB_EOF'
#!/usr/bin/env bash
SHORTSTAT="${STUB_GIT_SHORTSTAT:-}"
NAMES="${STUB_GIT_NAMES:-}"

# Detect diff --staged subcommands
if [ "$1" = "diff" ]; then
    for arg in "$@"; do
        if [ "$arg" = "--shortstat" ]; then
            echo "$SHORTSTAT"
            exit 0
        fi
        if [ "$arg" = "--name-only" ]; then
            # Print each name on its own line (split on spaces)
            if [ -n "$NAMES" ]; then
                for name in $NAMES; do
                    echo "$name"
                done
            fi
            exit 0
        fi
    done
fi

# Pass through to real git
if [ -x "/usr/bin/git" ]; then
    exec /usr/bin/git "$@"
elif [ -x "/c/Program Files/Git/bin/git" ]; then
    exec "/c/Program Files/Git/bin/git" "$@"
else
    exec git.exe "$@" 2>/dev/null || exit 128
fi
STUB_EOF
    chmod +x "$STUB_DIR/git"
}

create_stub_jq() {
    cat > "$STUB_DIR/jq" << 'STUB_EOF'
#!/usr/bin/env bash
exec "$HOME/.local/bin/jq" "$@"
STUB_EOF
    # Substitute $HOME literally in the stub
    sed -i "s|\$HOME|$HOME|g" "$STUB_DIR/jq"
    chmod +x "$STUB_DIR/jq"
}

create_stub_python3() {
    cat > "$STUB_DIR/python3" << 'STUB_EOF'
#!/usr/bin/env bash
TRIGGER="${STUB_PYTHON3_TRIGGER:-}"
if [ -n "$TRIGGER" ]; then
    echo "$TRIGGER"
    exit 0
fi
exec python3 "$@"
STUB_EOF
    chmod +x "$STUB_DIR/python3"
}
