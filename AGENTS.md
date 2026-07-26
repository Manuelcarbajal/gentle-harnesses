# Code Review Rules

## Hook scripts (bash)

- Source `gentle_ai.sh` for shared utilities — never duplicate `gentle_ai_bin()` or logging helpers
- Fail-open pattern: if `gentle-ai`, `codegraph`, or `jq` are absent, print an advisory JSON and exit 0
- Exit 2 only from PreToolUse scripts, with `{"decision":"block","reason":"..."}` on stdout
- All exit paths must produce valid JSON on stdout — no silent exits
- Hook timeout budgets: sum of all subprocess timeouts must stay below hook wall-clock limit
- Two-line guard for env vars that may be unset: assign first, then use — avoid `${VAR:-default}` inside complex expansions
- `systemMessage` for user-visible warnings; advisory context goes in `hookSpecificOutput.additionalContext` (nested, not top-level)

## Tests (bats)

- Each test stubs external binaries (gentle-ai, git, codegraph, jq) via env vars from `helpers.bash` — never call real binaries
- One test file per hook script
- Test every exit path: allow (0), block (2), and fail-open (0 on missing dependency)
- Golden output tests use `assert_output` from bats-assert, not manual string matching
