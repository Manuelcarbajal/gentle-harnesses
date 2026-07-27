# Changelog

All notable changes to gentle-claude are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

---

## [0.2.0-beta.6] - 2026-07-26

### Changed

- **Pi context filter extended** — `skills/gentle-ai/SKILL.md` now also disambiguates
  `gentle-ai-explore/worker/verify`, `pi-subagents`, `ask_user_question`, and
  `/gentle:sdd-preflight` references found in vendor assets, extending the filter first
  added in beta.1.

### Fixed

- **`CONTRIBUTING.md`** no longer references a nonexistent `log_info` helper — points at
  `gentle_ai_review_status` instead.

### Removed

- Hardcoded developer-machine path and dead `python3`-stub scaffolding from
  `tests/bats/helpers.bash`, leftover from the pre-bash-migration era.

---

## [0.2.0-beta.5] - 2026-07-26

### Added

- **Local release runbook** — `plugin/claude-code/skills/release/SKILL.md` overrides the
  vendored `gentle-pi` release skill (npm publish process) with the actual gentle-claude
  mechanism: tag push -> `release.yml` -> GitHub Release, no npm involved.

### Changed

- **`gentle-ai install`/`sync` now owns skill-registry refresh** — removed the duplicate
  hook declaration from `hooks.json` that fired the same refresh a second time per prompt
  for anyone who also ran `gentle-ai install`. Narrowed `vendor/gentle-pi`'s sparse-checkout
  to drop the 10 skills, 20 agents, and 1 doc that `gentle-ai` already installs natively in
  the correct Claude Code format.
- **Pre-commit gate bridged to `gentle-ai review status`** — `pre-tool-use.sh` now reads the
  risk tier from a read-only `review status` call (`.frozen.tier`, when an applicable receipt
  exists) instead of relying solely on the local `classify_diff()` heuristic, which stays as a
  documented fallback for when no receipt applies or the CLI is unavailable. Reads status
  rather than calling the mutating `review start` from inside the gate, per the ecosystem's
  own review-integration contract (gates must never launch review actors).

### Fixed

- **Silent `subagent-stop.sh` / `session-stop.sh` failures** — `subagent-stop.sh` shelled out
  to a nonexistent `gentle-ai mem` subcommand, silently no-op'ing every `SubagentStop` event;
  it now nudges the agent via `additionalContext` to call `mem_capture_passive` itself, since a
  hook process can't invoke MCP tools directly. `session-stop.sh` built its warning
  `systemMessage` inside a backgrounded subshell after `exit 0`, so Claude Code never received
  it; it now runs synchronously before exit.

---

## [0.2.0-beta.4] - 2026-07-26

### Changed

- **Repo/marketplace renamed to `gentle-harnesses`** — the repo hosts gentle-ai harness
  adapters for coding-agent CLIs/editors generally, not just Claude Code; `gentle-ai-claude`
  undersold that. The `gentle-claude` plugin's own `name` is unchanged (it's the stable
  install identifier), so existing installs keep working — only the marketplace identifier
  changed: `gentle-claude@gentle-claude` -> `gentle-claude@gentle-harnesses`.
- **`AGENTS.md` / `CLAUDE.md` restructured** — root `AGENTS.md` now holds the repo-wide,
  tool-agnostic facts (structure, conventions, dependencies) that any coding agent (Codex,
  Cursor, etc.) can read natively; root `CLAUDE.md` is a thin `@AGENTS.md` import plus the
  one genuinely Claude-Code-specific note, per Anthropic's own documented pattern for
  avoiding duplication between the two files. `plugin/claude-code/AGENTS.md` keeps the
  bash/bats review rules that are specific to this one harness, and `gga`'s `RULES_FILE`
  points at it.

### Fixed

- **Stale GitHub templates** — `.github/pull_request_template.md` and
  `.github/ISSUE_TEMPLATE/bug_report.md` still referenced pre-migration Python script paths
  and `pytest`; updated to the current bash paths under `plugin/claude-code/` and `bats`.

---

## [0.2.0-beta.3] - 2026-07-26

### Fixed

- **Post-compaction recovery never fired** — `post-compaction.sh` read a `trigger` field
  that Claude Code never sends (the real `SessionStart` payload field is `source`) and
  compared it against `"post_compact"` instead of the real value `"compact"`; the hook
  silently no-op'd on every session. Rewritten to parse `source` via `jq` and added
  `"matcher": "compact"` to its `hooks.json` entry so it only runs on compaction.
- **Documentation audit** — corrected install instructions across README/CONTRIBUTING
  (`claude plugin install --directory` is not a real flag; replaced with
  `plugin marketplace add` + `plugin install <name>@<marketplace>`), fixed the
  vendor sparse-checkout listing and `plugin.json` path references in
  ARCHITECTURE/DEVELOPMENT, and documented the marketplace `source` `./`-prefix
  requirement and immutable-tag convention in DEVELOPMENT.md

### Added

- **NOTICE** — formal MIT attribution for gentle-pi (Copyright Mario Zechner), covering
  the vendored submodule and the prompts/skill adapted from it

---

## [0.2.0-beta.2] - 2026-07-25

### Fixed

- **Marketplace plugin source** — `source` in `.claude-plugin/marketplace.json` was
  missing the required `./` prefix for relative paths, breaking plugin installs
- **CI bats suite** — the jq stub in `tests/bats/helpers.bash` hardcoded
  `$HOME/.local/bin/jq`, which only exists on the dev machine; on CI (jq at
  `/usr/bin/jq`) the stub failed and `pre-tool-use.sh` silently fell back to
  fail-open, masking every gate and safety-guard test

---

## [0.2.0-beta.1] - 2026-07-25

### Added

- **Hook scripts (bash)** — full hook coverage: `session-start.sh`, `user-prompt-submit.sh`,
  `pre-tool-use.sh`, `session-stop.sh`, `post-compaction.sh`, `subagent-stop.sh`
- **Risk-based diff classification** — `classify_diff()` in `pre-tool-use.sh` routes staged
  changes into LOW (docs only → skip gate), MED (standard → validate), or HIGH
  (>400 lines or high-risk paths → validate) before applying the review gate
- **Safety guards** — `classify_command()` hard-denies destructive commands (`rm -rf /`,
  force-push to main, `DROP TABLE`, `.env` overwrite) and requires confirmation for
  reversible-but-risky ones (`git reset --hard`, recursive deletes, force-push non-main)
- **Harness identity skill** — `plugin/claude-code/skills/gentle-ai/SKILL.md` defines the
  Claude Code adapter identity, review lifecycle, delegation protocol, memory rules, and SDD
  entrypoint as a discoverable skill injected into agent context
- **Operational prompts** — `gpr.md` (PR review), `gcl.md` (changelog audit), `gis.md`
  (issue analysis), `gwr.md` (wrap-up workflow) adapted from gentle-pi for Claude Code
- **bats test suite** — 47 tests across all hook scripts with a per-test stub system
  (gentle-ai, git, codegraph, python3, jq); dependencies installed on demand via
  `plugin/claude-code/tests/install-deps.sh`
- **gentle-pi as sparse git submodule** — `vendor/gentle-pi/` materializes only
  `skills/`, `prompts/`, `contracts/`, and `assets/` via sparse checkout; TypeScript
  runtime and Pi-specific directories are excluded
- **Vendor skill injection** — `inject_adapter_skills()` in `user-prompt-submit.sh` appends
  plugin and vendor skills to the official gentle-ai skill registry per prompt; plugin skills
  take priority over same-named vendor skills via two-pass deduplication
- **Lazy asset manifest** — `inject_asset_manifest()` emits a path manifest of
  `vendor/gentle-pi/assets/` sub-assets (delegation, memory, skills, SDD workflow, chains)
  so agents load file content only when the workflow applies
- **Pi-context filter** — section in `skills/gentle-ai/SKILL.md` that disambiguates
  Pi-specific references (`subagent_run`, `~/.pi/`, Pi mono-repo paths) found in vendor
  assets from their Claude Code equivalents
- **Binary local-first resolution** — `gentle_ai_bin()` checks `$CLAUDE_PLUGIN_ROOT/bin/`
  before falling back to PATH
- **Ecosystem health check** — `session-start.sh` validates `gentle-ai` binary, runs
  `gentle-ai doctor`, and checks for `codegraph` on every session start
- **Review gate** — `pre-tool-use.sh` blocks `git commit` when no valid review receipt
  exists (skipped for LOW-tier diffs)

### Changed

- Migrated all hook scripts from Python to bash — eliminates the Python 3 runtime
  dependency for hooks; only bash, jq, and the gentle-ai binary are required
- Restructured plugin files under `plugin/claude-code/` layout for multi-platform
  extensibility

### Removed

- Python hook scripts (`gentle_ai.py`, `pre-tool-use.py`, `session-start.py`,
  `session-stop.py`, `user-prompt-submit.py`) — replaced by bash equivalents
- Python test suite (`conftest.py`, `test_*.py`) — replaced by bats

---

## Format reference

Sections per version (in order): `Breaking Changes`, `Added`, `Changed`, `Fixed`,
`Deprecated`, `Removed`, `Security`.
