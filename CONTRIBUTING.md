# Contributing

## Prerequisites

- [Claude Code](https://claude.ai/code) CLI
- [`gentle-ai`](https://github.com/Gentleman-Programming/gentle-ai) in PATH
- Python 3.x

Optional but tested against:

- [`gga`](https://github.com/Gentleman-Programming/gga) — pre-commit hook
- [`codegraph`](https://github.com/Gentleman-Programming/codegraph) — code intelligence
- [`engram`](https://github.com/Gentleman-Programming/engram) — session memory

## Local install

```bash
git clone https://github.com/Manuelcarbajal/gentle-ai-claude.git
cd gentle-ai-claude
claude plugin install --directory .
```

To reload after editing a hook script:

```
/reload-plugins
```

## Dev environment

Install test dependencies:

```bash
pip install -r requirements-dev.txt
```

Run the test suite:

```bash
pytest
```

Copy the hook environment reference for manual testing:

```bash
cp .env.example .env
```

## Before opening a PR

All changes require a passing gentle-ai review receipt. Run the full cycle on your staged changes:

```bash
gentle-ai review start --cwd . --projection staged
# run the 4R lenses as instructed
gentle-ai review finalize --cwd . --lineage <id> --evidence <file>
gentle-ai review validate --gate pre-commit --cwd .
```

Only then commit and push. The PR template will ask you to confirm the receipt.

## Hook script contract

Each script in `scripts/` must:

- Exit `0` and print valid JSON on success
- Exit `2` with `{"decision": "block", "reason": "..."}` to block a tool (PreToolUse only)
- Never raise an uncaught exception — wrap all subprocess calls in try/except
- Be fail-open: if `gentle-ai`, `engram`, or `gga` are missing, exit `0` cleanly
- Be importable as a module — use `main()` + `if __name__ == "__main__": main()`

## Commit style

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
fix(session-start): add encoding guard for Windows subprocess output
feat(pre-tool-use): block git push without review receipt
docs: update installation instructions
test: add coverage for gate() fail-open paths
```
