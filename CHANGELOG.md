# Changelog

All notable changes to gentle-claude are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

---

## [0.1.0] - 2026-07-25

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
