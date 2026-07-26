# Contributing

## Prerequisites

- [Claude Code](https://claude.ai/code) CLI
- [`gentle-ai`](https://github.com/Gentleman-Programming/gentle-ai) in PATH
- `bash`, `jq`

Optional but tested against:

- [`gga`](https://github.com/Gentleman-Programming/gga) — pre-commit hook
- [`codegraph`](https://github.com/Gentleman-Programming/codegraph) — code intelligence
- [`engram`](https://github.com/Gentleman-Programming/engram) — session memory

## Local install

```bash
git clone --recurse-submodules https://github.com/Manuelcarbajal/gentle-ai-claude.git
cd gentle-ai-claude
claude plugin marketplace add .
claude plugin install gentle-claude@gentle-claude
```

To reload after editing a hook script:

```
/reload-plugins
```

## Dev environment

See [DEVELOPMENT.md](DEVELOPMENT.md) for full setup, test runner, and vendor update instructions.

Quick start:

```bash
bash plugin/claude-code/tests/install-deps.sh
bash plugin/claude-code/tests/run_bats.sh
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

Each script in `plugin/claude-code/scripts/` must:

- Exit `0` on all non-blocking paths (fail-open)
- Exit `2` with `{"decision": "block", "reason": "..."}` to block a tool (PreToolUse only)
- Print valid JSON to stdout on every path
- Never block if `gentle-ai`, `codegraph`, or `jq` are missing — check availability first
- Source `gentle_ai.sh` for shared utilities (`gentle_ai_bin`, `log_info`, etc.)

## Commit style

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
fix(pre-tool-use): guard against empty CLAUDE_TOOL_INPUT
feat(hooks): add subagent-stop hook
docs: update installation instructions
test: add coverage for classify_diff LOW tier
```
