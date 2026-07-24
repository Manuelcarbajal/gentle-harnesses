# Code Review Rules

## Python

- Use type annotations on all function signatures
- Subprocess calls: use `shutil.which()` to detect binaries that are Windows `.CMD`/`.bat` wrappers before calling them (e.g., `gga`, `codegraph`); for regular binaries, catching `FileNotFoundError` in the caller is sufficient
- Fail-open pattern: `FileNotFoundError` and `TimeoutExpired` must not block operations
- Return empty string `""` on skip/no-issue; return non-empty string on actionable issue
- Hook timeout budgets: sum of all subprocess timeouts must stay below hook wall-clock limit
- No bare `except Exception` outside of hook scripts where silent-fail is the contract

## Hook scripts

- Each script must exit cleanly (exit 0) on all non-blocking paths
- PreToolUse scripts exit 2 to block a tool call, 0 to allow
- Hook output must be valid JSON on stdout: `systemMessage`, `hookSpecificOutput`, or `{"decision":"block","reason":"..."}`
- `systemMessage` for user-visible warnings; `additionalContext` for advisory context only
