# gentle-ai-claude

A [Claude Code](https://claude.ai/code) plugin that wires the [gentle-ai](https://github.com/Gentleman-Programming/gentle-ai) ecosystem into your Claude sessions — health checks, skill registry injection, review lifecycle enforcement, and session continuity via Engram.

Mirrors what [gentle-pi](https://github.com/Gentleman-Programming/gentle-pi) does for the Pi coding agent.

## What it does

| Hook | Behavior |
|---|---|
| **SessionStart** | Checks gentle-ai binary, ecosystem health (`gentle-ai doctor`), codegraph binary, and codegraph MCP config. Auto-installs the GGA pre-commit hook if `gga` is available. Injects the last session snapshot from Engram as context. |
| **UserPromptSubmit** | Refreshes the skill registry (`.atl/skill-registry.md`) and injects it as context. Adds review lifecycle status and active SDD phase on every prompt. Surfaces a blocking `systemMessage` when a review is required before committing. |
| **PreToolUse** | Blocks `git commit` and `git push` when no valid review receipt exists for the current workspace. Fail-open: if `gentle-ai` is unavailable, commits are never blocked. |
| **Stop** | Validates the review gate on session end. Saves a session summary to Engram under the key `session-end:{project}` for recovery at the next SessionStart. |

## Requirements

- [Claude Code](https://claude.ai/code) — CLI or desktop app
- [`gentle-ai`](https://github.com/Gentleman-Programming/gentle-ai) binary in PATH
- Python 3.x (for hook scripts)

Optional but recommended:

- [`codegraph`](https://github.com/Gentleman-Programming/codegraph) — structural code intelligence (checked at SessionStart)
- [`engram`](https://github.com/Gentleman-Programming/engram) — session memory (snapshot injection and save)
- [`gga`](https://github.com/Gentleman-Programming/gga) — Gentleman Guardian Angel pre-commit hook (auto-installed per repo)

## Installation

```bash
git clone https://github.com/Manuelcarbajal/gentle-ai-claude.git
claude plugin install --directory gentle-ai-claude
```

Or add it to your `~/.claude/settings.json` directly:

```json
{
  "enabledPlugins": {
    "gentle-claude@gentle-claude": true
  },
  "extraKnownMarketplaces": {
    "gentle-claude": {
      "source": {
        "path": "/path/to/gentle-ai-claude",
        "source": "directory"
      }
    }
  }
}
```

## How it works

All hooks are Python scripts in `scripts/`. They fail-open — if any dependency (`gentle-ai`, `engram`, `gga`) is missing or times out, the hook exits cleanly without blocking Claude.

Hook output follows the Claude Code hook protocol:
- `systemMessage` for blocking/unmissable warnings
- `hookSpecificOutput.additionalContext` for advisory context
- `{"decision": "block", "reason": "..."}` with exit 2 for PreToolUse gates

## Review enforcement

The PreToolUse hook blocks `git commit` and `git push` until a valid `gentle-ai` review receipt exists for the staged content. The full cycle is:

```
gentle-ai review start --cwd .
# run 4R lenses (risk, resilience, readability, reliability)
gentle-ai review finalize --cwd . --lineage <id> [--evidence <file>]
gentle-ai review validate --gate pre-commit --cwd .
git commit
```

## Project structure

```
.claude-plugin/plugin.json   Plugin metadata
hooks/hooks.json             Hook declarations
scripts/session-start.py     SessionStart hook
scripts/user-prompt-submit.py UserPromptSubmit hook
scripts/pre-tool-use.py      PreToolUse gate
scripts/session-stop.py      Stop hook
AGENTS.md                    GGA code review rules
```

## License

MIT — Manuel Carbajal
