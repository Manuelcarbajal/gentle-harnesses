# Changelog

All notable changes to gentle-claude are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

---

## [0.2.0-beta.11] - 2026-07-31

### Added

- **`/gentle-review` skill — the supported native review path for Claude Code**
  (`plugin/claude-code/skills/gentle-review/SKILL.md`). Drives the gentle-ai negotiated review
  lifecycle entirely from the main thread (which has full `Bash`) instead of dispatching the
  `review-*` lens subagents. Those subagents cannot run the mandated frozen-tree `git diff`/`cat-file`
  inspection (no `Bash` grant), and Claude Code has no seam to inject the frozen trees into a
  subagent, so the reviewer work runs in the orchestrator thread and results are submitted through
  the binary's additive headless capability, `gentle-ai review capture-result`. The skill routes
  strictly from the native `next_transition`, keeps the byte-exact frozen-tree inspection, handles
  the `consent/v2` blocking envelope (`--locale es`), and plugs into the existing
  `pre-tool-use.sh` receipt gate. It documents the one accepted tradeoff — a single actor reviewing
  has no blind adversarial separation — and points high-risk changes at `judgment-day` (two blind
  judges, which works natively because its judges read files directly rather than through the
  frozen-tree contract).

### Changed

- **`skills/gentle-ai/SKILL.md` now hands off review execution to `/gentle-review`.** The
  "Review lifecycle" section points the model at the `/gentle-review` skill as the way to actually
  run a review in Claude Code — disambiguating it from the other "review"-named skills and steering
  away from the non-functional `review-*` subagent path.

### Removed

- **Stale "Vendor asset context" section dropped from `skills/gentle-ai/SKILL.md`.** It documented
  how to filter Pi-specific references when loading `vendor/gentle-pi/` files, but since beta.9
  removed all vendor content injection — `inject_adapter_skills()` reads only local plugin skills,
  and vendor skill dirs are no longer checked out — that guidance was orphaned: the harness never
  points the model at vendor files. Verified against the live injector and its bats coverage.

---

## [0.2.0-beta.10] - 2026-07-31

### Fixed

- **`UserPromptSubmit` hook timeouts under Windows/Git Bash.** `gentle_ai_review_status()`'s
  internal `gentle-ai review status` call is bounded by `timeout 6` (was `5`) to give it a
  realistic chance to complete instead of being killed before returning useful data. The plugin
  hook's own budget in `hooks.json` is raised from `10s` to `15s` to leave headroom for Windows
  process-spawn overhead on top of that call. Root cause was `gentle-ai` 2.2.1's per-path git
  subprocess fan-out in `review status`; upgrading to 2.2.4 (git path query batching, review
  startup no longer materializing the full repository path inventory) cut the call's real-world
  duration roughly in half, and these timeout values are calibrated against the faster binary.

---

## [0.2.0-beta.9] - 2026-07-31

### Fixed

- **`vendor/gentle-pi`'s sparse-checkout was never actually persisted** — the scope lived only
  under `.git/modules/vendor/gentle-pi/info/sparse-checkout` (local git plumbing, never
  committed by `git add vendor/gentle-pi`), so `.github/workflows/{ci,release}.yml` and every
  fresh clone always checked out the full, untrimmed submodule regardless of prior local
  narrowing. Tracked the pattern list at `plugin/claude-code/scripts/vendor-sparse-checkout.patterns`
  and added `sync-vendor-sparse-checkout.sh` to apply it, wired into both CI workflows and
  documented in `DEVELOPMENT.md`.

### Removed

- **`inject_asset_manifest()` removed entirely from `user-prompt-submit.sh`.** Every remaining
  `vendor/gentle-pi` content source turned out to be dead weight or actively counterproductive:
  the 2 vendor skill dirs were always shadowed by same-named local plugin skills; the 4 agent
  docs (`gentle-ai-explore/worker/verify`, `review-validator`) were referenced by nothing
  anywhere in the repo, and 3 of the 4 are explicitly flagged as Claude-Code-inapplicable Pi
  noise by `skills/gentle-ai/SKILL.md`'s own context filter; `docs/review-integration.md`
  itself substantively duplicates the review-orchestration instructions `gentle-ai install`
  already writes into `~/.claude/CLAUDE.md` (confirmed by direct comparison and by completing
  two full native review cycles this session without reading it). `vendor/gentle-pi` now checks
  out only root files (`LICENSE`, `README.md`, etc, kept for MIT compliance and provenance) —
  zero functional content dependency remains.

### Changed

- **`vendor/gentle-pi` bumped to `5fe1beaa`** (v2.1.2 + 11 upstream commits; diffed first, no
  structural changes to any tracked path).
- **`HARNESS-AUDIT.md` refreshed and committed** for the first time — previously kept as
  local-only working notes. Stale Phase 5 checkboxes corrected (were unchecked despite shipping
  in beta.6), Phase 6 marked resolved (contracts dependency removed rather than migrated), and a
  new SS16 living-changelog section added covering beta.5 through this release.

---

## [0.2.0-beta.8] - 2026-07-31

### Fixed

- **`user-prompt-submit.sh` crashed with a raw `jq: command not found` instead of degrading
  gracefully** — every other `jq` call in this script (and the sibling `pre-tool-use.sh`) checks
  `command -v jq` first; the final `hookSpecificOutput` build was the one path without a guard.
  Now exits cleanly when `jq` is unavailable, matching the rest of the hook.

### Changed

- **`vendor/gentle-pi` updated to v2.1.2** (from v1.2.0-1, 13 upstream commits).
- **`inject_asset_manifest()` no longer injects vendor content gentle-ai already provides
  natively** — delegation rules, memory protocol, skills discovery, SDD workflow, review chains,
  TDD support docs, and the skill style guide are all Pi-specific originals with a
  Claude-Code-adapted equivalent already installed globally by `gentle-ai` (confirmed via direct
  diff). Only `docs/review-integration.md` and the 4 `gentle-ai-*`/`review-validator` agent docs
  remain, since those have no native gentle-ai equivalent.

---

## [0.2.0-beta.7] - 2026-07-26

### Fixed

- **`release` skill silently bypassed the native `gentle-ai review validate --gate release`
  check** — the gate requires five release-evidence inputs
  (`--release-configuration`, `--release-provenance`, `--release-generated`,
  `--release-publication-boundary`, `--release-evidence-freshness`) that the runbook never
  supplied, so every past release skipped it. `plugin/claude-code/skills/release/SKILL.md` now
  generates minimal, honest evidence reflecting this repo's actual release path (no build, git
  commit/tag as provenance, GitHub Release via `release.yml` as the publication boundary, zero
  generated artifacts) and validates the gate before tagging.

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
