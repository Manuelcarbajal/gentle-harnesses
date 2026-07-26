---
description: gentle-claude harness — review lifecycle, risk routing, delegation, and SDD protocol for Claude Code
---

# gentle-claude

Claude Code adapter for the gentle-ai ecosystem. Enforces review discipline, SDD workflow, and delegation protocol.

## Review lifecycle

1. When starting work on any repo, run `gentle-ai review status --cwd <cwd>` to check for an existing receipt.
2. After implementation is complete, run `gentle-ai review start` to open a bounded review.
3. Before committing, run `gentle-ai review validate --gate pre-commit --cwd <cwd>`.
4. Before pushing or opening a PR, run `gentle-ai review validate --gate pre-push --cwd <cwd>`.

## Risk-based lens selection

Determine tier from the diff before starting review:

- **LOW** — only docs, comments, or formatting; zero executable code or config changes → skip review, commit directly.
- **MEDIUM** — all other changes → run exactly ONE lens: risk > resilience > reliability > readability.
- **HIGH** — any of: >400 changed lines, or paths matching `auth`, `security`, `payments`, `secrets`, `credentials`, `update`, `deploy`, `migrations`, or shell/process integration → run full 4R (risk + resilience + reliability + readability).

Generated golden files are excluded from the line count but remain in snapshot identity.

## Delegation protocol

| Trigger | Action |
|---|---|
| Reading 4+ files to understand | Delegate an exploration agent |
| Writing 2+ non-trivial files | Delegate a single writer agent |
| ~20 tool calls without delegation, growing complexity | Pause and delegate remaining work |

Do not run parallel writers unless isolated worktrees are explicitly approved.

## Memory

Use engram MCP proactively — do not wait to be asked:

- `mem_save` — after any decision, bug fix, discovery, convention, or config change
- `mem_search` / `mem_context` — when any past work is referenced
- `mem_session_summary` — before saying "done"

## SDD

For complex, risky, or ambiguous work: use SDD phases — explore → propose → spec → design → tasks → apply → verify → archive.

For simple tasks with a clear, bounded scope: skip SDD entirely.

When in doubt about complexity, use `/sdd-explore` before starting implementation.
