# Harness Audit — Philosophy, Boundaries, and Long-Term Architecture

Status: **Analysis complete, roadmap partially executed** (analysis date: 2026-07-26,
last refreshed: 2026-07-31 — see §16 for what shipped since the original analysis)

Architectural review of `gentle-claude` and everything vendored from `gentle-pi`, checked
against the real `gentle-ai` source code (Go module cached locally at
`gentleman-programming/gentle-ai@v1.49.0`, also verified against the installed binary
v2.1.11) — not against assumptions about what it "should" have.

---

## 0. Core finding: Gentle-AI is already multi-host — the problem isn't "adapting", it's "not duplicating"

The question that guided this analysis was "who owns what?". The answer changed halfway
through, after reading the real `gentle-ai` source code:

**Gentle-AI already has a native adapter abstraction for 16 hosts** —
`internal/agents/interface.go` defines an `Adapter` with methods like `SkillsDir`,
`SubAgentsDir`, `SettingsPath`, `MCPStrategy`, and `internal/agents/factory.go` wires
concrete implementations for Claude Code, Cursor, Codex, Windsurf, Pi, OpenCode, Gemini
CLI, VS Code Copilot, Kilocode, Kimi, Qwen Code, Kiro, Antigravity, OpenClaw, Trae, and Hermes.

Even more: **gentle-ai already packages and natively installs almost all of the same
skills and agents that `vendor/gentle-pi/` re-brings via sparse submodule.**
`internal/assets/skills/` contains `branch-pr`, `chained-pr`, `cognitive-doc-design`,
`comment-writer`, `issue-creation`, `judgment-day`, `skill-creator`, `skill-improver`,
`skill-registry`, `work-unit-commits`, and the 7 SDD skills. `internal/assets/claude/agents/`
already ships, in the correct Claude Code subagent format (capitalized tool names, not
Pi's lowercase vocabulary), the four review lenses, the three Judgment Day roles, and the
twelve SDD agents — natively installed into `~/.claude/agents/` via `gentle-ai install`/`sync`.

This reframes the problem. It isn't about deciding "what to vendor from gentle-pi", but
recognizing that **a large part of `vendor/gentle-pi/assets/agents/` and several vendored
skills are, with very high probability, a second copy — with broken format (frontmatter in
Pi's tool dialect, not Claude Code's) — of something `gentle-ai install` already places
correctly in `~/.claude/`.** The harness doesn't need to reinvent or re-vendor that layer;
it needs to rely on it and limit itself to what no cold `install` can give it: live hook
wiring inside a running Claude Code session.

A second finding of equal weight: **there is already literal, not conceptual,
duplication.** `internal/components/sdd/inject.go:1454-1504` installs a `UserPromptSubmit`
hook into `~/.claude/settings.json` that runs, verbatim,
`gentle-ai skill-registry refresh --quiet --no-gitignore --cwd "${CLAUDE_PROJECT_DIR:-$PWD}" || true`
— the exact same command, character for character, that
`plugin/claude-code/hooks/hooks.json:26-34` already declares as the plugin's first
`UserPromptSubmit` hook. A user who ran `gentle-ai install` for Claude Code *and* installed
the gentle-claude plugin triggers that command twice per prompt.

---

## 1. Official project philosophy

**Gentle Harnesses connects the Gentle-AI ecosystem to hosts that have their own live
session lifecycle — one Gentle-AI cannot reach by installing files cold.** Its only reason
to exist is that gap: hooks that fire during a real session (startup, every prompt, every
tool call, subagent end, shutdown), translating the specific host contract into calls
against `gentle-ai`'s stable CLI.

### What the mission IS

- Translate a specific host's hook contract (payload format, environment variables, how
  to block/allow an action) into `gentle-ai` commands.
- React to events that only happen in real time inside the session (a `Bash` call, a
  `git commit`, a subagent finishing) — none of this exists yet at the time of
  `gentle-ai install`.
- Fill, in an explicitly temporary and documented way, gaps the native CLI doesn't yet
  cover (the correct example already exists in this very repo: `inject_adapter_skills()`
  carries a `REMOVE this function if gentle-ai adds native support for these paths`
  comment).

### What the mission is NOT

- It is not reimplementing the review engine, risk classification, the skill registry, or
  the agent model — that already exists in `gentle-ai` and, for several cases, is also
  already packaged natively for Claude Code specifically.
- It is not maintaining a second copy of platform-agnostic content (skills, agents,
  contracts) just because gentle-pi brings it — if gentle-ai already installs it natively,
  re-vendoring it is dead weight with a desync risk.
- It is not becoming the place where memory, SDD, or review identity for the ecosystem
  lives — those remain the responsibility of gentle-ai / engram, exactly as
  `MIGRATION-RESEARCH.md` already correctly states ("gentle-claude should not try to own
  memory either").

---

## 2. Architectural principles

1. **Single source of truth for all ecosystem policy.** Risk thresholds, the dangerous
   command taxonomy, skill registry format: they live in exactly one place, `gentle-ai`.
   If a harness needs that logic, it invokes it — it doesn't rewrite it in bash,
   TypeScript, or anywhere else.
2. **Before vendoring, check if it's already native.** Any "platform-agnostic" content
   that's a candidate for `vendor/` must first be checked against gentle-ai's
   `internal/assets/`. If it's already there in the correct format for the host, it isn't
   vendored — it's documented as a `gentle-ai install` dependency.
3. **Everything vendored temporarily must be labeled as removable**, with the exact
   removal condition (e.g. "remove when gentle-ai exposes X"). The pattern already exists
   in this repo (`inject_adapter_skills()`); it should be generalized, not treated as the
   exception.
4. **The harness translates protocols, it doesn't invent security policy.** When, by
   design, policy must live in the host (e.g. the destructive-command guard, which
   `gentle-ai` itself intentionally declares out of its own scope), its content must have
   a single versioned source shared across hosts — not a manual per-adapter copy that can
   silently diverge.
5. **No hook should fail silently against a nonexistent command.** A `|| true` that
   swallows an `unknown command` isn't "fail-open", it's an invisible bug with zero test
   coverage.
6. **One test per hook script, no exceptions.** The harness's own `AGENTS.md` already
   requires this; it needs to be enforced, not just stated.

---

## 3. Gentle-AI's responsibilities (verified in code, not assumed)

| Capability | Evidence | Real status |
|---|---|---|
| Multi-host adapter abstraction (16 hosts) | `internal/agents/interface.go`, `factory.go:25-52` | Native and complete |
| Config/skills/agents install-sync per host | `internal/cli/install.go`, `sync.go`, `internal/components/skills/inject.go` | Native and complete |
| Skill registry format (`.atl/skill-registry.md`) | `internal/skillregistry/registry.go:19-105` | Native, closed format (see §5) |
| Review engine (start/finalize/validate/status), v1 contract | `gentle-ai review --help`, `internal/reviewtransaction/` | Native — the installed CLI (v2.1.11) exposes the unified surface; the risk classifier (`ClassifyRisk`) exists as a library but isn't wired into any command in the audited source (v1.49.0) |
| Review agents (4R), Judgment Day, SDD — content and deployment | `internal/assets/claude/agents/*.md`, installed via `SubAgentsDir` | Native, correct Claude Code subagent format |
| Agnostic skills (branch-pr, chained-pr, comment-writer, etc.) | `internal/assets/skills/*` | Native |
| SDD slash commands for Claude Code | `internal/assets/claude/commands/*.md` | Native — matches the `sdd-*` skills already installed |
| `doctor` (ecosystem health) | `internal/cli/doctor.go:41,70-84` | Native — 4 checks (known binaries, `state.json`, engram HTTP, disk). `codegraph` wasn't in the known-binaries list in v1.49.0; needs reconfirming against v2.1.11 |
| "release" skill (gentle-pi npm publishing) | absent from `internal/assets/skills/` | **Does not exist natively** — genuinely Pi-specific |
| Session-lifecycle hooks (Claude Code's SessionStart, PreToolUse, SubagentStop, Stop) | grep returns nothing in `internal/` beyond the single-point `UserPromptSubmit` injection | **Does not exist** — exactly the gap the harness must fill |

---

## 4. Gentle Harnesses' responsibilities (and only these)

- **Live hook wiring**: `hooks.json` + the bash scripts Claude Code runs on every session
  event.
- **Host payload translation**: parsing `CLAUDE_TOOL_NAME`, `CLAUDE_TOOL_INPUT`,
  `CLAUDE_PLUGIN_ROOT`, the `SessionStart`/`PreToolUse` JSON, and returning the output
  shapes Claude Code expects (`systemMessage`, `hookSpecificOutput`, `decision:block`).
- **Local binary resolution** (`$CLAUDE_PLUGIN_ROOT/bin/gentle-ai` before `PATH`).
- **Operational prompts adapted** to this repo's actual shape (gpr/gcl/gis/gwr without
  Pi's monorepo paths) — genuinely per-host content, not a sharing candidate.
- **Single-command packaging and install** via `.claude-plugin/marketplace.json` —
  Claude Code-specific distribution mechanics.
- **Temporary, labeled filling** of point gaps in the CLI (while they exist).

Everything else — risk policy, the dangerous-command taxonomy as a single source,
platform-agnostic skill/agent content, review contracts — doesn't belong to the harness,
not even temporarily, unless it's documented as a loan with an expiration date.

---

## 5. Folder-by-folder analysis — native gentle-claude code

### `plugin/claude-code/hooks/hooks.json`
**KEEP.** Well-defined responsibility: wires 6 hook registrations against 5 Claude Code
events. The only weak spot is that the skill-registry `UserPromptSubmit` literally
duplicates what `gentle-ai install` can already write into `~/.claude/settings.json` (see
§0) — a roadmap decision, not a design problem with the file itself.

### `plugin/claude-code/scripts/gentle_ai.sh`
**KEEP.** The best-written file in the repo: thin process-invocation wrappers, verified
live against the installed CLI's real output shape. Zero policy logic of its own.

### `plugin/claude-code/scripts/session-start.sh`
**ADAPT.** Mostly correct. One redundant check: it verifies `command -v codegraph`
separately from `gentle_ai_doctor` — redundant only if `doctor` already covers
`codegraph` in the installed version (unconfirmed).

### `plugin/claude-code/scripts/user-prompt-submit.sh`
**ADAPT.** `inject_adapter_skills()` and `inject_asset_manifest()` are the correct pattern
for temporary duplication: they're explicitly marked for removal. The one real gap is that
only the `next_transition.kind == "review.start"` state is surfaced as blocking; the
`"collect"` state (ambiguous lineage) falls through to the generic message.

### `plugin/claude-code/scripts/pre-tool-use.sh`
**Main finding of the entire audit.** `classify_diff()` (lines 26-51) reimplements a
LOW/MED/HIGH classifier from scratch — the same work that, per its own help text,
`gentle-ai review start` does ("derive the bounded review tier, lenses, and correction
budget"). But **no hook in this repo ever calls `review start`** — only
`review validate --gate pre-commit/pre-push` is invoked, which validates an existing
receipt, not creates one. This means the bash copy isn't a local shortcut later confirmed
by the CLI: today, it's the sole automatic arbiter of whether the review gate even
applies. `classify_command()` (lines 56-98) additionally reimplements, in bash, the same
hard-deny/confirm/allow taxonomy that gentle-pi separately maintains in TypeScript
(`classifyGuardedCommand()`) — with no shared versioned source between the two copies.

### `plugin/claude-code/scripts/post-compaction.sh`
**KEEP.** Correctly scoped to payload translation; the historical bug (compared against a
nonexistent `trigger` field) is already fixed and covered by a test.

### `plugin/claude-code/scripts/subagent-stop.sh`
**Broken in production.** Runs `"$bin" mem capture --passive --quiet` — `gentle-ai mem`
doesn't exist as a subcommand (confirmed live: `Error: unknown command "mem"`). The
`2>/dev/null || true` swallows the error, so the hook is a silent no-op on every run,
contradicting this repo's own decision to "delegate memory to Engram MCP" that the rest
of the codebase respects. No test coverage (`test_subagent_stop.bats` doesn't exist),
despite `AGENTS.md` requiring one test per script.

### `plugin/claude-code/scripts/session-stop.sh`
**TO VERIFY.** The warning `systemMessage` is emitted inside a background subshell (`&`)
after the hook has already returned `exit 0` — it's likely that message never actually
displays, because Claude Code reads the hook's output at the moment the process exits, not
from a background job. The current test only checks the exit code, not whether the message
is delivered.

### `plugin/claude-code/skills/gentle-ai/SKILL.md`
**KEEP.** Correct harness identity; the memory section correctly delegates to Engram MCP.
The risk block restates the same `classify_diff()` thresholds in prose — the fifth
restatement of the same policy across the whole ecosystem (bash, this skill, README, the
vendored Pi skill, and the original `lib/review-risk.ts`).

### `plugin/claude-code/prompts/*.md` (gpr, gcl, gis, gwr)
**KEEP.** Legitimate adaptation: they drop Pi's monorepo paths, keep the structure. The
one gap: they lack the YAML frontmatter their vendored originals have, and there's no
confirmation in the repo that Claude Code registers them as real `/gpr` commands — worth
verifying before assuming they're "live".

### `.claude-plugin/plugin.json` + `marketplace.json`
**KEEP.** Correct metadata, version synced with `CHANGELOG.md`.

### `plugin/claude-code/tests/`
**ADAPT.** 47 real tests, solid coverage of `classify_command`/`classify_diff`. Concrete
gap: zero coverage of `subagent-stop.sh` (exactly the broken script). `helpers.bash`
carries a hardcoded path from the developer's machine and Python-era scaffolding that's no
longer used.

### Root docs (`README`, `CONTRIBUTING`, `DEVELOPMENT`, `CHANGELOG`, `docs/flow.md`)
**KEEP.** Consistent with each other and with actual behavior. One minor drift:
`CONTRIBUTING.md` mentions a `log_info` helper that doesn't exist in any script.

### `md/MIGRATION.MD` (gitignored)
**DELETE.** Predates the bash→Python rewrite by hours, diagnoses defects in `.py` files
that no longer exist, and its incremental remediation plan was made obsolete by the full
rewrite that actually happened. It's no-man's-land: invisible in git, but a wrong map for
anyone who finds it on disk.

### `.github/workflows/ci.yml`, `release.yml`
**KEEP.** Minimal, correct automation, no embedded ecosystem policy.

---

## 6. Full analysis of `vendor/gentle-pi/`

Sparse submodule that materializes only `skills/`, `prompts/`, `contracts/`, `assets/`,
`docs/`. Every row was read in full and checked against gentle-ai's `internal/assets/`.

### `skills/` — 12 folders + `_shared`

| Skill | Already native in gentle-ai? | Verdict |
|---|---|---|
| `branch-pr`, `chained-pr`, `cognitive-doc-design`, `comment-writer`, `issue-creation`, `judgment-day`, `skill-creator`, `skill-improver`, `skill-registry`, `work-unit-commits` | Yes — confirmed byte-for-byte in `internal/assets/skills/` | Redundant with native |
| `gentle-ai/SKILL.md` (Pi version) | N/A — it's Pi's identity | Correctly suppressed by the local skill |
| `release/SKILL.md` | **No** — confirmed absent from `internal/assets/skills/` | Misuse risk (see finding below) |
| `_shared/review-ledger-contract.md` | A better-maintained copy exists in `internal/assets/skills/_shared/` | Orphaned, unreachable by the current injection pattern |

**The vendored `release` skill is gentle-pi's npm publishing runbook**
(`pnpm publish --dry-run`, `gh workflow run publish.yml --repo Gentleman-Programming/gentle-pi`),
and since there's no local override with that name, it gets injected as-is into any
project using gentle-claude — including gentle-claude itself, whose actual release is
tag → GitHub Release, no npm. This is the highest-severity finding in the entire
vendor/ analysis: actively wrong instructions, not just dead weight.

### `prompts/`
**KEEP as reference**, not injected (correct decision, documented in `NOTICE`). Four of
five already have a local adapted copy; `skill-creation.md` is the only one left
unadapted — minor gap, low priority.

### `contracts/review-integration/v1/` — 18 files (8 schemas + 10 fixtures)
**TO MOVE.** This is, literally, the `gentle-ai` binary's own wire protocol
(`$id: https://gentle-ai.dev/contracts/...`) — it doesn't belong to gentle-pi or
gentle-claude. Today nothing in this repo parses or validates it; only the string
identifier `gentle-ai.review-integration/v1` is passed to the CLI. Natural candidate to
live directly in the `gentle-ai` repo (or be consumed from there), not to arrive
secondhand via gentle-pi.

### `assets/orchestrator*.md`, `chains/`, `support/`, `agents/`
**MIXED.** `orchestrator.md` is correctly excluded from injection (unresolved
`{{GENTLE_PI_*}}` placeholders, Pi identity). `orchestrator-delegation.md` and
`sdd-orchestrator-workflow.md` mix genuinely reusable content (delegation threshold
table, SDD phase model) with Pi-exclusive names not covered by the current context filter
in `SKILL.md` (`gentle-ai-explore/worker/verify`, `ask_user_question`,
`/gentle:sdd-preflight`). `support/strict-tdd*.md` and `sdd-status-contract.md` are
agnostic and high-value. The 26 files in `assets/agents/` have frontmatter in Pi's tool
vocabulary (lowercase, `find`/`webfetch`/`mem_*`) that Claude Code doesn't interpret —
**22 of those 26 already exist, in the correct format, in gentle-ai's
`internal/assets/claude/agents/`**; only `gentle-ai-explore/worker/verify` and
`review-validator.md` have no confirmed native equivalent.

### `assets/migrations/*.json`, `assets/gentle-logo-only.png`
**DELETE.** gentle-pi's npm installer checksum manifests and the badge logo — zero
references anywhere in the repo, an inevitable side effect of directory-level sparse
checkout.

### `docs/`
`review-integration.md` and `skill-style-guide.md`: **keep**, agnostic and actively
loaded. `native-authority-architecture.md`: **remove from the lazy manifest** — it's an
internal engineering report on gentle-pi's TypeScript rewrite, zero actionable content
for a Claude Code session.

### Submodule root (`package.json`, `pnpm-lock.yaml`, `pnpm-workspace.yaml`, `.gitattributes`, `.gitignore`)
**Inert** — side effect of sparse checkout for an npm package that's never installed
here. `LICENSE` is the exception: **mandatory**, cited by the root `NOTICE` for MIT
compliance. `README.md`: inert but legitimate as provenance documentation.

---

## 7. Resources that should be deleted

- `md/MIGRATION.MD` — obsolete, contradicts the real state of the code.
- Vendored `skills/_shared/review-ledger-contract.md` — orphaned, a better version
  already exists natively in gentle-ai.
- `docs/native-authority-architecture.md` from the lazy-load manifest (the file can stay
  materialized by the sparse checkout, but shouldn't be injected).
- The `log_info` reference in `CONTRIBUTING.md` — a helper that doesn't exist.
- Hardcoded developer-machine path in `tests/libs`/`helpers.bash`, and Python stub
  scaffolding no longer used by any current script.

## 8. Resources that should remain

- The 6 hook scripts and `gentle_ai.sh` (with the point fixes from roadmap phases 0/3).
- `plugin/claude-code/skills/gentle-ai/SKILL.md` — the harness's identity, irreplaceable.
- The 4 adapted operational prompts (`gpr`, `gcl`, `gis`, `gwr`).
- `vendor/gentle-pi/skills/gentle-ai/SKILL.md` (Pi version) — correctly suppressed, zero
  real cost.
- `vendor/gentle-pi/assets/support/*`, `orchestrator-memory.md`,
  `docs/review-integration.md`, `docs/skill-style-guide.md` — agnostic and valuable, even
  if someday promoted to gentle-ai they remain correct here in the meantime.
- Vendored `LICENSE` — legal obligation.
- The entire test suite (with the `subagent-stop.sh` gap closed).

## 9. Resources that should move to Gentle-AI

- The full `contracts/review-integration/v1/` — it's the binary's own protocol;
  vendoring it via gentle-pi is an indirect path for something gentle-ai could publish or
  expose directly.
- The 10 agnostic skills already natively duplicated (`branch-pr`, `chained-pr`,
  `cognitive-doc-design`, `comment-writer`, `issue-creation`, `judgment-day`,
  `skill-creator`, `skill-improver`, `skill-registry`, `work-unit-commits`) — they don't
  need "moving" because they **already are** in gentle-ai; what needs to move is
  gentle-claude's dependency, from "vendor from gentle-pi" to "trust
  `gentle-ai install`".
- The 22 agents in `assets/agents/` with a confirmed native equivalent — same logic.
- The `classify_command()` taxonomy (hard-deny/confirm/allow) — today it lives
  separately in bash (gentle-claude) and TypeScript (gentle-pi); it needs a single
  versioned source, and the natural place is gentle-ai, since neither host should be the
  authority.

## 10. Resources that should be reused directly (already native — stop vendoring)

This is the category that changes the most compared to the original framing: these
aren't resources to promote in the future, **they already exist today** in installed
`gentle-ai`, in a better format than the vendored copy:

- The 4 review lenses (`review-risk`, `review-readability`, `review-reliability`,
  `review-resilience`) + `review-refuter`.
- The 3 Judgment Day roles (`jd-judge-a`, `jd-judge-b`, `jd-fix-agent`).
- The 12 SDD phase agents (`sdd-apply` … `sdd-verify`) and their corresponding slash
  commands.
- The skill registry format (`.atl/skill-registry.md`) and its generation via
  `gentle-ai skill-registry refresh`.

The condition for "stop vendoring" isn't automatic: it requires confirming that a
`gentle-ai install`/`sync` for Claude Code is a documented prerequisite of the harness
(today it isn't — the harness installs on its own, via the marketplace, without depending
on having run the CLI beforehand). That's exactly the trade-off resolved in the roadmap
(phase 2).

## 11. Strategy to minimize maintenance

1. **A single "parity" test against the installed CLI.** Before every release, a bats
   test should run real `gentle-ai --help`/`gentle-ai doctor` and compare against what
   the scripts assume (command names, JSON fields) — so a CLI that changes its surface
   breaks CI instead of breaking silently in production, as already happened with
   `gentle-ai mem`.
2. **Remove every policy restatement without a single source.** Risk thresholds are
   today written 5 times (bash, SKILL.md, README, the vendored Pi skill, the original
   TypeScript). Changing a threshold requires editing 5 places by hand; nothing enforces
   that today.
3. **Trust `gentle-ai install`/`sync` instead of re-vendoring.** Reduces the surface of
   files this repo has to keep in sync with gentle-pi.
4. **Delete documentation that no longer describes the code**
   (`md/MIGRATION.MD`) the moment it goes stale, not months later.

## 12. Strategy to avoid future duplication

- **Mandatory checklist before vendoring or writing new logic:** does it already exist in
  gentle-ai's `internal/assets/` or `internal/cli/`? If yes, don't copy it — document it
  as a dependency.
- **Everything vendored temporarily carries an explicit removal condition** in the file
  itself or in `ARCHITECTURE.md`, following the pattern already used in
  `inject_adapter_skills()`.
- **No harness reimplements its own risk or security classifier** — it only consumes
  what gentle-ai exposes, or, if gentle-ai deliberately delegates that policy to the host
  (like the command guard), that policy lives in a single repo shared across hosts, not
  copied per adapter.
- **Periodic review of gentle-ai's `internal/assets/` against `vendor/`** — every
  gentle-ai release may have "caught up" content that's still vendored out of habit.

---

## 13. Refactoring roadmap (actionable checklist)

### Phase 0 — Active bugs
These are silent breakages today, not design questions — fix before touching
architecture.

- [ ] Fix `subagent-stop.sh`: remove the call to nonexistent `gentle-ai mem`, delegate
      passive capture to the agent itself via `mem_capture_passive` (MCP), not via shell
- [ ] Add `test_subagent_stop.bats`
- [ ] Verify whether `session-stop.sh`'s async `systemMessage` actually displays; if not,
      redesign message delivery

### Phase 1 — `release` skill risk
The only finding that can lead to an actively incorrect action (publishing to the wrong
repo/package).

- [x] Create `plugin/claude-code/skills/release/SKILL.md` with gentle-claude's real
      runbook (tag → GitHub Release), same pattern already used for `gentle-ai/SKILL.md`

### Phase 2 — Dependency decision
The decision that unblocks the rest of the `vendor/` cleanup.

- [x] Decide whether the harness requires `gentle-ai install`/`sync` as a documented
      prerequisite
- [x] If yes: remove the skill-registry hook duplication in `hooks.json`
- [x] Start retiring the skills/agents from `vendor/` that are already native (see §10)

### Phase 3 — Bridge to `review start`
Removes the riskiest duplication (review security policy) without losing the local
fail-safe.

- [x] Make `pre-tool-use.sh` read the tier via `gentle-ai review status` (read-only) when
      an applicable receipt exists — never invoke `review start` from the gate (would
      violate the `vendor/gentle-pi/docs/review-integration.md` contract)
- [x] Use the tier the CLI returns
- [x] Keep `classify_diff()` as a documented fallback if the CLI doesn't respond — not as
      the sole arbiter

### Phase 4 — Single source for `classify_command()`
Depends on coordination with the gentle-ai maintainer (org `Gentleman-Programming`, no
relation to this repo's owner) — no real communication channel or track record for a
cross-repo proposal to succeed today.

- [ ] Propose a canonical versioned list of dangerous patterns (JSON/YAML) to gentle-ai
- [ ] Consumed by both gentle-claude and gentle-pi

**Attempted and reverted (2026-07-26):** re-scoping the phase to a local extraction was
tried — `classify_command()` reading its own `command-risk-patterns.json` via `jq`,
instead of the 8 rules in bash. It worked (55/55 tests) but was scrapped after weighing
cost/benefit: it doesn't solve the actual duplication with gentle-pi (the problem this
phase exists to fix), and `classify_command()` runs on **every** Bash command in this
repo (not just risky ones), so the redesign added up to ~33 `jq` forks per invocation to
the hot path of every command — a measurable cost on Windows, for a minor maintainability
gain on 8 fixed rules that rarely change. Reverted to inline bash. Not worth solving this
phase alone; it stays parked until real coordination with gentle-ai exists.

### Phase 5 — vendor/ cleanup
Low risk, high clarity value — done in parallel with the above.

- [x] Remove `docs/native-authority-architecture.md` from the lazy manifest (already
      handled by Phase 2's sparse-checkout narrowing — nothing to do)
- [x] Extend the Pi context filter in `SKILL.md` (cover `gentle-ai-explore/worker/verify`,
      `pi-subagents`, `ask_user_question`, `/gentle:sdd-preflight`)
- [x] Delete `md/MIGRATION.MD`
- [x] Fix the `log_info` reference in `CONTRIBUTING.md`
- [x] Clean up the hardcoded path and dead Python scaffolding in
      `tests/libs`/`helpers.bash`

Shipped `6fda08c` (2026-07-26), released in `v0.2.0-beta.6`.

### Phase 6 — Contracts
Depends on gentle-ai — coordinated in parallel, doesn't block the rest of the roadmap.

- [x] Evaluate with gentle-ai whether `contracts/review-integration/v1/` can be consumed
      directly from its repo/release instead of via gentle-pi

**Resolved differently than planned (2026-07-31):** the cross-repo coordination gap never
closed (same blocker as Phase 4 — no real channel with the gentle-ai maintainer). But a
full vendor re-audit (§16) confirmed nothing in this repo ever parsed those 18 files —
only the string identifier `gentle-ai.review-integration/v1` is passed to the CLI (§6
already noted this). So the checklist item resolved by removing the dependency rather
than by moving it: `contracts/` is excluded from the sparse checkout entirely, and this
repo carries zero copy of the wire protocol, vendored or otherwise.

---

## 14. Target v1.0 architecture and multi-host support

```
gentle-ai  (engine + native 16-host adapter + packaged skills/agents)
   │
   │  install / sync writes config, skills, and native agents per host
   ▼
~/.claude/, ~/.cursor/, ~/.codex/, ~/.windsurf/, ...  (already solved by gentle-ai, no harness)

   ┌─ for hosts WITH their own session lifecycle (live hooks) ─┐
   │                                                             │
   ▼                                                             ▼
gentle-harnesses/plugin/claude-code/     gentle-harnesses/plugin/<host>/
   hooks.json + bash scripts                 same pattern, different host
   (ONLY protocol translation,                hook/event protocol
    no ecosystem policy)
```

The original question — "how should the repo be organized if `gentle-cursor`,
`gentle-codex`, `gentle-windsurf` show up tomorrow?" — has a narrower answer than the
name suggests: **gentle-ai already solves Cursor, Codex, and Windsurf at the install
level** (the 16 adapters in `internal/agents/` already cover them). A new
`plugin/<host>/` inside `gentle-harnesses` is only justified for hosts that, like Claude
Code, expose a session-time hook mechanism worth wiring — if a host doesn't have that
mechanism, it needs no harness at all, `gentle-ai install` is enough.

For those that do need it, the structure already adopted
(`plugin/<host>/{hooks,scripts,skills,prompts,tests}/`) is correct and scales without
changes — each host folder is a thin adapter, none of them vendor agnostic content
separately. The current `vendor/gentle-pi/` should, medium-term, shrink to what no other
mechanism covers: content genuinely specific to Pi (that doesn't apply to any other host)
and nothing else — everything agnostic becomes a `gentle-ai install` dependency, shared
by every `plugin/<host>/` without any of them having to re-bring it.

---

## 15. Appendix — Session economics (delegation, cache, `/clear`)

Note added during execution of Phase 0 of this roadmap, with real data from that
execution — not projections.

### 15.1 Delegating to subagents doesn't save tokens — it saves your own context

The Phase 0 fix (two ~15-line scripts + two test files) was delegated to a subagent per
`CLAUDE.md`'s explicit rule ("2+ non-trivial files → delegate"). Real measured cost:
**106,067 tokens and 47 tool calls** in the subagent, plus the overhead of building the
delegation prompt, reading the report, and re-reading the 4 files to verify. Doing it
inline would have cost a fraction of that — the fix was already diagnosed with the exact
line from the audit, there was nothing to "explore".

**Conclusion:** delegating optimizes *my own* context window in a long session (it keeps
the full content of read files from staying pinned in history and pushing toward
compaction sooner), not total token cost — which usually goes up, not down. `CLAUDE.md`'s
file-count threshold rule doesn't weigh the task's real size/complexity; for small,
already-diagnosed fixes, delegating is money thrown away.

### 15.2 Per-session capacity — there's no hard token ceiling

Sonnet 5 (`claude-sonnet-5`) runs with a **1M token** context window (that value is both
the default and the maximum — not a separate tier to activate) and 128K max output
tokens. Claude Code additionally layers its own automatic compaction on top: as the
conversation grows, old context gets automatically summarized and work continues without
interruption — there's no point where the session "cuts off" by size.

What actually limits things in practice:

- **Cost, not available tokens.** The API is *stateless* — every request resends the full
  history. With prompt caching active, that history is served mostly from cache (~0.1x
  the cost of normal input) — but every compaction event rewrites a chunk of history into
  a summary, which invalidates the cached prefix at that point and forces an expensive
  cache write (1.25x–2x) for everything that follows. Very long sessions with frequent
  compactions pay that cost repeatedly.
- **Fidelity loss.** A compaction summary is lossy — fine details from old exchanges
  (an exact line number, the exact wording of a decision) can get lost or approximated
  poorly after summarizing.

### 15.3 When to run `/clear`

It's not a token-count decision — it's a task-boundary decision:

- **Run `/clear` when starting genuinely unrelated work** (a different project, a
  different goal). Avoids paying to resend/cache irrelevant history and entirely avoids
  the compaction cost on that old content.
- **Don't run `/clear` in the middle of a related work thread** (like this session:
  audit → fixes → commit → this very note). Losing that context forces re-deriving
  everything already established — much more expensive than letting automatic compaction
  summarize it.
- If the work is a sustained initiative across a whole day, let automatic compaction do
  its job instead of clearing manually — that's exactly what it's for.

---

## 16. Progress since the original analysis (2026-07-26 → 2026-07-31)

This section is the living continuation of §13's roadmap — updated as phases ship instead
of staying frozen at the analysis date. Detailed evidence for each item lives in Engram
(`gentle-harnesses` project); this is the compressed trail.

**Releases:**
- `v0.2.0-beta.5` (`6e37f43`) — Phases 0-3: silent hook bugs fixed, `release` skill
  written, dependency decision made, `pre-tool-use.sh` bridged to `gentle-ai review
  status` (read-only, never `review start` from the gate — see the Phase 3 note above
  about the contract violation a first attempt hit and how it was corrected).
- `v0.2.0-beta.6` (`075aa27`) — Phase 5 vendor cleanup (checkboxes above updated to
  match) plus the Phase 4 attempt-and-revert written up as parked docs.
- `v0.2.0-beta.7` (`c5d8c8a`) — first release where the `release` gate was genuinely
  satisfied (not bypassed): `gentle-ai review validate --gate release` wants 5
  release-evidence categories with no fixed schema; `skills/release/SKILL.md` now
  generates minimal-but-honest JSON for each instead of leaving the gate unsatisfiable.
- `v0.2.0-beta.8` (`be1e11a`) — `user-prompt-submit.sh`'s final `jq` call guarded
  (`eeb1af8`); `vendor/gentle-pi` bumped to `v2.1.2` (`08bec6e`, v1→v2 review-integration
  contract migration noted but deferred — this repo's 3 `gentle_ai.sh` call sites stay on
  v1, which the installed CLI still resolves); `inject_asset_manifest()` stopped injecting
  `orchestrator-delegation.md`, `orchestrator-memory.md`, `orchestrator-skills.md`,
  `sdd-orchestrator-workflow.md`, the 4 `chains/*.chain.md`, and `support/*.md` (`4105514`)
  — **a bigger native-coverage finding than §10 originally scoped**: not just the 4
  categories §10 lists, but the whole orchestrator/delegation/memory/SDD-workflow/TDD/
  review-chain layer, because `gentle-ai install`'s *global* Claude Code output
  (`~/.claude/CLAUDE.md`'s Agent Teams Lite section, `skills/_shared/`,
  `skills/sdd-{apply,verify}/`, `skills/skill-creator/references/`, the native
  `review-*` agents backing `judgment-day`) already covers all of it, adapted for Claude
  Code rather than left in Pi's dialect. §6's "MIXED" verdict on
  `assets/orchestrator*.md`/`chains/`/`support/` is superseded by this finding.

**2026-07-31 session (uncommitted at analysis-refresh time — see repo history for the
actual landing commit):**
- Re-audited `vendor/gentle-pi`'s working tree against `inject_asset_manifest()`/
  `inject_adapter_skills()` post-beta.8 and found the trim above left 12 files checked out
  but referenced by nothing: the 4 orchestrator/SDD-workflow docs, all 4 `chains/`, all 3
  `support/`, and `docs/skill-style-guide.md` (§6/§8 above still call the last one "keep,
  actively loaded" — that was true pre-beta.8, stale after it). Sparse-checkout narrowed
  from 19 tracked paths to the 7 that are genuinely read: `docs/review-integration.md`,
  the 4 `assets/agents/{gentle-ai-explore,gentle-ai-worker,gentle-ai-verify,
  review-validator}.md`, and `skills/{gentle-ai,release}/SKILL.md`.
- **Found the sparse-checkout mechanism itself was never real.** It lives under
  `.git/modules/vendor/gentle-pi/info/sparse-checkout`, which is local git plumbing —
  `git add vendor/gentle-pi` only stages the submodule's pinned commit, never the
  checkout scope. `.github/workflows/{ci,release}.yml` both do a plain
  `submodules: recursive` checkout with no sparse-checkout applied. So every phase-2/4/5
  "narrowing" up to this point only ever affected this one local clone — CI and any fresh
  clone always got the full, untrimmed `vendor/gentle-pi`. Fixed by tracking the pattern
  list at `plugin/claude-code/scripts/vendor-sparse-checkout.patterns` and adding
  `sync-vendor-sparse-checkout.sh` to apply it, wired into both CI workflows and
  documented in `DEVELOPMENT.md`.
- **Known follow-up, not yet fixed:** `ARCHITECTURE.md:95-113` and `docs/flow.md:65-74`
  still describe `inject_asset_manifest()` emitting the 8 orchestrator/chain paths that
  `4105514` removed — stale documentation of the pre-beta.8 behavior.
- **Pending, undecided:** `vendor/gentle-pi`'s working tree was manually fast-forwarded
  to `5fe1beaa` (11 commits past the pinned `v2.1.2`/`3b6b3d2` — none touch tracked
  paths' file *structure*, only content: `docs/review-integration.md` gained a refined
  `--consent declined` authorization model and a `--locale` flag; the 4 vendored
  `review-*.md` agents changed too but this repo excludes them and uses its own local
  agents). The outer repo's gitlink is still pinned at `3b6b3d2` — whether to formally
  bump the pin is an open decision as of this refresh.

---

*Analysis based on direct reading of `ARCHITECTURE.md`, `MIGRATION-RESEARCH.md`,
`NOTICE`, all 6 hook scripts, the 26 files in `vendor/gentle-pi/assets/agents/`, the 12
vendored skills, the 18 files in `contracts/review-integration/v1/`, and the real
`gentle-ai@v1.49.0` source code (Go module cached locally) checked against the installed
v2.1.11 binary. Interactive version with navigation and tables: see the artifact
published in this conversation.*
