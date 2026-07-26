# Migration Research

Status: **COMPLETE — migration implemented and validated**

This document tracks the research phase for the upcoming restructuring of `gentle-claude`.
All reference repos have been analyzed. Decisions are finalized below.

---

## Goal

Transform `gentle-claude` into a professional, discoverable Claude Code plugin that:

- Follows the structural conventions of the Gentleman-Programming ecosystem
- Is installable via the Claude Code marketplace in one command
- Serves as the official reference integration for Gentle-AI + Claude Code

---

## Repos Analyzed

### 1. Gentleman-Programming/engram

**URL:** https://github.com/Gentleman-Programming/engram
**Role in ecosystem:** Persistent memory — the "brain" layer. Agent-agnostic Go binary.

#### Key Takeaways

**Structure:**
```
plugin/claude-code/
  .claude-plugin/   ← marketplace.json
  hooks/            ← hooks.json
  scripts/          ← .sh hook scripts
  skills/memory/
  .mcp.json
```

**Shell scripts, not Python:** Zero extra dependencies. Engram uses `.sh` — no Python runtime required.

**marketplace.json:** One-command install via `claude plugin marketplace add Gentleman-Programming/engram`.
gentle-claude has no `marketplace.json` — invisible in the marketplace.

**Hooks present that gentle-claude is missing:**
| Hook | Engram | gentle-claude |
|---|---|---|
| `SessionStart (startup)` | ✅ | ✅ |
| `SessionStart (compact)` | ✅ `post-compaction.sh` | ❌ |
| `UserPromptSubmit` | ✅ | ✅ |
| `SubagentStop` | ✅ | ❌ |
| `Stop` (async) | ✅ | sync only |

**CONTRIBUTING:** Issue-first methodology with automated PR validation.
**CHANGELOG:** Auto-generated via GoReleaser from conventional commits.

---

### 2. Gentleman-Programming/gentle-pi

**URL:** https://github.com/Gentleman-Programming/gentle-pi
**Role in ecosystem:** THE direct analog — same adapter role, but for Pi instead of Claude Code.
**Stats:** 201 stars, 51 forks, 4,257 commits, npm:gentle-pi@1.2.0

#### Key Takeaways

**This is the most important reference.** gentle-pi does exactly what gentle-claude does:
adapts gentle-ai to run inside a specific agent (Pi). Studying its decisions is studying
what the mature version of gentle-claude should look like.

**Package distribution via npm:**
```bash
pi install npm:gentle-pi@0.14.0
```
gentle-pi is an npm package — versioned, pinnable, installable in one command.
gentle-claude is a raw git repo — no versioning, no package manager, manual install.

**Bundles gentle-ai binary locally:**
```
lib/gentle-ai-binary.ts  ← package-local binary, no PATH dependency
```
gentle-pi ships the gentle-ai binary inside the package. No `gentle-ai` in PATH required.
gentle-claude requires `gentle-ai` in PATH — fragile, especially on fresh installs.

**TypeScript extensions, not scripts:**
```
extensions/
  gentle-ai.ts      ← identity, review orchestration, SDD, safety guards
  skill-registry.ts ← auto-discovery of .atl/skill-registry.md
  codegraph-tools.ts
  sdd-init.ts
  startup-banner.ts
```
Logic lives in typed extensions, not ad-hoc scripts. Testable, maintainable.

**Strict separation of concerns:**
- gentle-pi = workflow discipline + review gates + SDD
- gentle-engram = memory (separate package — `pi install npm:gentle-engram`)
- gentle-pi does NOT provide memory — it delegates to engram

This is the right model. gentle-claude should not try to own memory either.

**Naming convention confirmed — `gentle-{platform}`:**
- `gentle-pi` → Pi agent
- `gentle-engram` → Engram tool
- `gentle-claude` → Claude Code

The naming convention `gentle-{platform}` IS the ecosystem standard.
`gentle-claude` is the correct name. The discoverability problem is NOT a naming
problem — it's a distribution problem (no marketplace.json, no npm package).

---

## Final Decisions

### Name: keep `gentle-claude`

`gentle-{platform}` is the ecosystem pattern. Changing it would break consistency.
The real fix is marketplace.json + proper distribution — not a rename.

### Distribution: marketplace.json (priority 1)

The single biggest gap. Without it, gentle-claude is invisible.
Target: `claude plugin marketplace add Gentleman-Programming/gentle-claude`

### gentle-ai binary: bundle locally (priority 2)

gentle-pi's approach — bundle the binary, no PATH dependency.
This eliminates the #1 install failure mode on fresh machines.

### Scripts: migrate from Python to shell (priority 3)

Reduces friction. No Python runtime needed. Follows engram's approach.
Caveat: current Python scripts are well-tested (55 tests). Migration requires
rewriting tests. Do incrementally, not all at once.

### Structure: adopt `plugin/claude-code/` layout (priority 4)

Follows engram's convention. Better organized for a repo that may later host
adapters for other agents (plugin/cursor/, plugin/windsurf/, etc.).

### Missing hooks: add in v0.2.0 (priority 5)

- `SessionStart (compact)` — context recovery after compaction
- `SubagentStop` — passive memory capture when subagents finish
- Make `Stop` async

### Review lens routing: token-conscious by design (priority 2b)

gentle-pi implementa un sistema determinístico de routing que minimiza consumo de tokens
asignando el menor número de lenses posible según el riesgo real del diff.

**Clasificación de riesgo (de `lib/review-risk.ts`):**

| Tier | Condición | Lenses |
|---|---|---|
| **LOW** | Solo docs, sin config, sin binarios | 0 lenses — cero costo |
| **MEDIUM** | Todo lo demás (default) | 1 lens — el de mayor riesgo dominante |
| **HIGH** | >400 líneas modificadas O paths de riesgo alto | 4 lenses completos (4R) |

**Señales de riesgo alto (paths) — dos mecanismos:**
- Frases (regex): `data[-_/ ]?(?:exposure|loss)|privilege[-_/ ]?escalation`
- Tokens (cualquier segmento del path): `auth|authentication|authorization|update|updater|security|payments?|permissions?|shell|process|secrets?|credentials?|tokens?`

**Para MEDIUM — lens dominante (orden de prioridad exacto):**

| Prioridad | Lens | Señales de path |
|---|---|---|
| 1 | `review-risk` | cualquier token/frase de riesgo alto |
| 2 | `review-resilience` | `update\|deploy\|deployment\|infra\|infrastructure\|ops\|migrations?\|rollback\|recovery` |
| 3 | `review-reliability` | `tests?\|specs?\|runtime\|api` o extensiones `.test`/`.spec` |
| 4 | `review-readability` | fallback por defecto |

**Budget de corrección:** `min(200, ceil(originalChangedLines / 2))`

**Lo que esto significa para gentle-claude:**
El hook `pre-tool-use.sh` actualmente bloquea en git commit/push sin discriminar el tamaño
ni el riesgo del cambio. Con este modelo, evalúa el diff antes de decidir si pedir
review completo (4R), review mínimo (1 lens) o dejar pasar sin review (solo docs).
Reduce drásticamente el consumo de tokens en cambios triviales.

---

### Scope boundary: don't own memory

gentle-pi doesn't provide memory — pairs with gentle-engram.
gentle-claude should take the same stance: wire the hooks, delegate memory to engram MCP.
No reimplementing what engram already does.

---

## Feature Parity — gentle-pi vs gentle-claude

Lo que gentle-pi tiene como adapter. Marcado por responsabilidad:
**A** = responsabilidad del adapter | **GA** = responsabilidad de gentle-ai (no reimplementar)

### Hooks

| Feature | gentle-pi | gentle-claude | Responsabilidad |
|---|---|---|---|
| SessionStart startup | ✅ | ✅ | A |
| SessionStart compact (post-compaction) | ✅ | ✅ | A |
| UserPromptSubmit | ✅ | ✅ | A |
| SubagentStop | ✅ | ✅ | A |
| Stop (async) | ✅ async | ✅ async | A |

### Distribución e instalación

| Feature | gentle-pi | gentle-claude | Responsabilidad |
|---|---|---|---|
| marketplace.json | ✅ npm package | ❌ | A |
| One-command install | ✅ `pi install npm:gentle-pi` | ❌ manual | A |
| Binary bundled localmente | ✅ `lib/gentle-ai-binary.ts` | ❌ PATH dep | A |
| Versioning semántico | ✅ 1.2.0 en npm | ❌ solo plugin.json | A |

### Review system

| Feature | gentle-pi | gentle-claude | Responsabilidad |
|---|---|---|---|
| Risk-based lens routing (LOW/MED/HIGH) | ✅ `lib/review-risk.ts` | ✅ `classify_diff()` en `pre-tool-use.sh` | A |
| 0 lenses para cambios triviales | ✅ | ✅ LOW → skip review | A |
| 1 lens para cambios estándar | ✅ | ✅ MED → validate pre-commit | A |
| 4R completo para high-risk / >400 líneas | ✅ | ✅ HIGH → validate pre-commit | A |
| Correction budget `min(200, ceil(lines/2))` | ✅ | ❌ | GA |
| Native authority binding | ✅ | ✅ vía gentle-ai CLI | GA |

### Safety guards

| Feature | gentle-pi | gentle-claude | Responsabilidad |
|---|---|---|---|
| Clasificación de comandos (allow/confirm/block) | ✅ `classifyGuardedCommand()` | ✅ `classify_command()` en `pre-tool-use.sh` | A |
| Hard-deny para comandos destructivos | ✅ | ✅ rm -rf /, force-push main, DROP TABLE, overwrite .env | A |
| Confirm para operaciones sensibles | ✅ | ✅ force-push non-main, reset --hard, rm -rf | A |

### Orchestrator assets

| Feature | gentle-pi | gentle-claude | Responsabilidad |
|---|---|---|---|
| `assets/orchestrator.md` | ✅ | ✅ vía `vendor/gentle-pi/assets/` | A |
| `assets/orchestrator-skills.md` | ✅ | ✅ vía vendor | A |
| `assets/orchestrator-memory.md` | ✅ | ✅ vía vendor | A |
| `assets/orchestrator-delegation.md` | ✅ | ✅ vía vendor | A |
| `assets/sdd-orchestrator-workflow.md` | ✅ | ✅ vía vendor | A |

### Chains (workflow shortcuts)

| Feature | gentle-pi | gentle-claude | Responsabilidad |
|---|---|---|---|
| `4r-review.chain.md` | ✅ | ✅ vía `vendor/gentle-pi/assets/chains/` | A |
| `sdd-full.chain.md` | ✅ | ✅ vía vendor | A |
| `sdd-plan.chain.md` | ✅ | ✅ vía vendor | A |
| `sdd-verify.chain.md` | ✅ | ✅ vía vendor | A |

### Agents (definiciones)

| Categoría | gentle-pi | gentle-claude | Responsabilidad |
|---|---|---|---|
| Gentle-AI (explore, verify, worker) | ✅ 3 agents | ✅ parcial vía skills | GA |
| Judgment Day (judge-a, judge-b, fix-agent) | ✅ 3 agents | ✅ vía skills | GA |
| Review (readability, reliability, resilience, risk, refuter, validator) | ✅ 6 agents | ✅ vía skills | GA |
| SDD (apply, archive, design, explore, init, onboard, proposal, spec, status, sync, tasks, verify) | ✅ 12 agents | ✅ vía skills | GA |

### Skills incluidas en el adapter

| Skill | gentle-pi | gentle-claude | Responsabilidad |
|---|---|---|---|
| branch-pr | ✅ | ✅ vía ~/.claude/skills | A |
| chained-pr | ✅ | ✅ | A |
| judgment-day | ✅ | ✅ | A |
| skill-creator / skill-improver | ✅ | ✅ | A |
| comment-writer | ✅ | ✅ | A |
| issue-creation | ✅ | ✅ | A |
| cognitive-doc-design | ✅ | ✅ | A |
| work-unit-commits | ✅ | ✅ | A |
| release | ✅ | ✅ vía `vendor/gentle-pi/skills/release/` | A |
| skill-registry | ✅ | ✅ | A |

### DX y experiencia

| Feature | gentle-pi | gentle-claude | Responsabilidad |
|---|---|---|---|
| Startup banner | ✅ `extensions/startup-banner.ts` | ❌ | A |
| Model routing por fase SDD | ✅ `~/.pi/gentle-ai/models.json` | ❌ | A |
| Persona configurable (gentleman/neutral) | ✅ | ✅ vía output style | A |
| Structured logging | ✅ | ❌ solo stderr prints | A |
| `doctor` command | ✅ vía gentle-ai CLI | ✅ en SessionStart | A |

---

### Resumen de gaps reales del adapter

Lo que gentle-claude necesita implementar (responsabilidad A):
**✅ = implementado | ❌ = pendiente**

1. ✅ `marketplace.json` — crítico
2. ✅ Binary local-first en `gentle_ai_bin()` — `$CLAUDE_PLUGIN_ROOT/bin/` antes de PATH
3. ✅ post-compaction hook
4. ✅ SubagentStop hook
5. ✅ Risk-based lens routing en `pre-tool-use.sh` — LOW/MED/HIGH via `classify_diff()`
6. ✅ Safety guards completos — `classify_command()`: hard-deny + confirm + allow
7. ✅ `skills/gentle-ai/SKILL.md` — harness identity + vendor Pi-context filter
8. ✅ Prompts operacionales (`gpr`, `gcl`, `gis`, `gwr`)
9. ✅ Orchestrator assets — vía `vendor/gentle-pi/assets/` (sparse submodule)
10. ✅ Chains — vía `vendor/gentle-pi/assets/chains/`
11. ✅ `release` skill — vía `vendor/gentle-pi/skills/release/`
12. ❌ Startup banner — bajo, no hay equivalente nativo en Claude Code
13. ❌ Model routing — bajo, conveniencia

Pendiente para completar la integración del vendor:
A. ❌ Registrar `vendor/gentle-pi/skills/` como fuente en `gentle-ai skill-registry`
B. ❌ Actualizar `user-prompt-submit.sh` para lazy-load de `vendor/gentle-pi/assets/`
C. ❌ CI/CD: `ci.yml` (bats) + `release.yml` (tag → GitHub Release)
D. ❌ Docs: `DEVELOPMENT.md`, `ARCHITECTURE.md`, `CHANGELOG.md`

---

## Migration Checklist

### Phase 0 — Foundations ✅
- [x] Create `.claude-plugin/marketplace.json`
- [x] Tag v0.1.0 in git + create GitHub Release
- [x] Add GitHub Topics: `gentle-ai`, `claude-code`, `plugin`, `review-lifecycle`, `skill-registry` — do via GitHub UI
- [ ] Write `CHANGELOG.md`

### Phase 1 — Structure ✅
- [x] Move plugin files under `plugin/claude-code/`
- [x] Keep root as project metadata (README, LICENSE, CONTRIBUTING, etc.)
- [x] Update `hooks/hooks.json` paths accordingly

### Phase 2 — Binary ✅
- [x] Update `gentle_ai_bin()` in `gentle_ai.sh` to check `$CLAUDE_PLUGIN_ROOT/bin/gentle-ai` first,
      fallback to `command -v gentle-ai` — mirrors `lib/gentle-ai-binary.ts` without SHA256 overhead
- [x] Document binary version pinning in README (which version ships bundled, how to override)

### Phase 3 — Missing Hooks ✅
- [x] Add `post-compaction.sh` (SessionStart compact matcher)
- [x] Add `subagent-stop.sh` (SubagentStop hook)
- [x] Make `session-stop.sh` async (non-blocking)

### Phase 4 — Scripts Migration ✅
- [x] Migrate `session-start.py` → `session-start.sh`
- [x] Migrate `user-prompt-submit.py` → `user-prompt-submit.sh`
- [x] Migrate `pre-tool-use.py` → `pre-tool-use.sh`
- [x] Migrate `session-stop.py` → `session-stop.sh`
- [x] Rewrite test suite for shell scripts (bats) — 47 tests in `tests/bats/`, runner at `tests/run_bats.sh`
      Infrastructure: bats-core 1.14.0 + bats-support + bats-assert installed via `tests/install-deps.sh`
      Libs excluded from repo (`tests/libs/` gitignored) — cloned on demand, not vendored
      Per-test stub system (gentle-ai, git, codegraph, python3, jq) controlled via env vars

### Phase 4b — Risk Routing & Safety Guards ✅
Derived from `lib/review-risk.ts` and `extensions/gentle-ai.ts` (`classifyGuardedCommand`).

- [x] Implement LOW/MED/HIGH classification in `pre-tool-use.sh` via `classify_diff()`:
      - LOW (only .md/.txt/.rst/.adoc staged) → skip review gate entirely
      - MED (everything else) → validate pre-commit gate
      - HIGH (>400 changed lines OR high-risk path tokens: auth, security, token, credential, etc.) → validate pre-commit gate
- [x] Expand safety guards via `classify_command()`:
      - Hard-deny: `rm -rf /`, `rm -rf /*`, `git push --force` to main/master, `DROP TABLE/DATABASE/SCHEMA`, overwrite `.env`
      - Confirm: `git push --force` (non-main), `git reset --hard`, `rm -rf <non-root>`
      - Allow: everything else
- [x] Bug fix: `${CLAUDE_TOOL_INPUT:-{}}` bash expansion appended extra `}` when var was set — replaced with two-line assignment guard

### Phase 5 — CI/CD + Docs ✅ (core complete)
- [x] GitHub Actions: `ci.yml` (bats on every PR, runs on ubuntu-latest with `--recurse-submodules`)
- [x] GitHub Actions: `release.yml` (tag → GitHub Release, extracts CHANGELOG entry)
- [x] Write `ARCHITECTURE.md`
- [x] Write `DEVELOPMENT.md` (clone with --recurse-submodules, run tests, vendor update, hook dev, release steps)
- [ ] Write `SECURITY.md` — low priority, no sensitive data handled
- [ ] Write `ROADMAP.md` — low priority
- [x] Write `CHANGELOG.md`

### Phase 6 — Harness Identity Skill & Prompts ✅
**This is the biggest token-efficiency gap.** gentle-pi defines the harness as a discoverable
SKILL that the skill registry injects dynamically. gentle-claude has no equivalent — its behavior
is hardcoded in a monolithic CLAUDE.md loaded every session regardless of need.

- [x] Create `skills/gentle-ai/SKILL.md` — defines what gentle-claude IS as a harness:
      identity, delegation rules, risk-based review, TDD protocol, SDD workflow pointer.
      Gets auto-discovered by `gentle-ai skill-registry refresh` and injected into context.
- [x] Create `prompts/gpr.md` — PR review workflow (add label, read diff, verify changelog,
      structured Good/Bad/Ugly output). Mirrors gentle-pi's `prompts/gpr.md`.
- [x] Create `prompts/gcl.md` — changelog audit before release (commits since last tag,
      cross-package changelog verification). Mirrors gentle-pi's `prompts/gcl.md`.
- [x] Create `prompts/gis.md` — issue creation with issue-first methodology.
- [x] Create `prompts/gwr.md` — work review prompt.

### Phase 4c — gentle-pi as Submodule ✅ (partial)
Skills in gentle-pi (`skills/`, `prompts/`, `contracts/`) are LLM-first and platform-agnostic —
they work in Claude Code without modification. Instead of duplicating them, gentle-claude references
gentle-pi directly as a git submodule so updates flow in with one command.

Sparse checkout — materializes only directories applicable to Claude Code:
  `skills/`, `prompts/`, `contracts/`, `assets/`, `docs/`

Complete directory inventory (all of gentle-pi):

  ✅ skills/     — 13 platform-agnostic skill definitions → injected via inject_adapter_skills()
  ✅ assets/     — orchestrator sub-assets, chains, 26 agent defs, support docs → lazy manifest
  ✅ contracts/  — review-integration v1 (fixtures/, schemas/) → used by gentle-ai CLI
  ✅ docs/       — review-integration.md, native-authority-architecture.md, skill-style-guide.md
                   → reference docs, platform-agnostic → added to lazy manifest
  ⚠️ prompts/   — in sparse (reference only); NOT injected — Pi-specific mono-repo paths
  ❌ runtime/    — .mjs Pi runtime files (Node.js) — NOT applicable
  ❌ openspec/   — Pi's own SDD artifacts (config.yaml, changes/, specs/) — NOT applicable
  ❌ extensions/ — TypeScript Pi TUI extensions — NOT applicable
  ❌ lib/        — TypeScript review library implementation — NOT applicable
  ❌ scripts/    — Node.js build and installer scripts — NOT applicable
  ❌ tests/      — Pi test suite — NOT applicable
  ❌ themes/     — Pi UI themes — NOT applicable

What's in vendor/gentle-pi/skills/ (now available without duplication):
  branch-pr, chained-pr, cognitive-doc-design, comment-writer, gentle-ai (Pi version — differs
  from local), issue-creation, judgment-day, release ← was ❌, now accessible via vendor
  skill-creator, skill-improver, skill-registry, work-unit-commits, _shared/

Note on prompts: vendor prompts are NOT replacements for local ones.
  - `vendor/gentle-pi/prompts/` — Pi-specific (hardcoded mono-repo paths: packages/ai/, etc.)
  - `plugin/claude-code/prompts/` — Claude Code adapted versions; these stay as-is

Note on skills/gentle-ai: local `plugin/claude-code/skills/gentle-ai/SKILL.md` defines the
  Claude Code harness identity. The vendor version defines the Pi harness. Both stay — different
  identities for different platforms.

- [x] `git submodule add https://github.com/Gentleman-Programming/gentle-pi.git vendor/gentle-pi`
      with sparse checkout: `git sparse-checkout set skills prompts contracts assets docs`
- [x] Register vendor skills via `inject_adapter_skills()` in `user-prompt-submit.sh`:
      reads official registry first (gentle-ai as primary source), then appends plugin/
      and vendor/gentle-pi/skills/ rows with scope "plugin"/"adapter". Deduplicates by
      name — local plugin skill wins over same-named vendor skill. Encapsulated in one
      removable function if gentle-ai adds native vendor/ support.
- [x] Add Pi-context filter to `skills/gentle-ai/SKILL.md`
- [x] Write `DEVELOPMENT.md` (includes: run tests, update submodule, add skills, hook dev)

### Phase 7 — Orchestrator Assets & Chains ✅ (via vendor)
Assets exist in `vendor/gentle-pi/assets/` — no local creation needed.
Chains (4r-review, sdd-full, sdd-plan, sdd-verify) have zero Pi-specific references.
Orchestrator files have marginal Pi refs (1–11 lines each) handled by the context filter in
`skills/gentle-ai/SKILL.md` (see Phase 4c).

Pi-specific reference counts per file:
  orchestrator.md: 5 | orchestrator-delegation.md: 11 | orchestrator-memory.md: 1
  orchestrator-skills.md: 2 | sdd-orchestrator-workflow.md: 8
  chains/4r-review.chain.md: 0 | chains/sdd-full.chain.md: 0

- [x] `assets/orchestrator.md` — available at `vendor/gentle-pi/assets/orchestrator.md`
- [x] `assets/orchestrator-delegation.md` — available via vendor
- [x] `assets/orchestrator-memory.md` — available via vendor
- [x] `assets/orchestrator-skills.md` — available via vendor
- [x] `assets/chains/4r-review.chain.md` — available via vendor (zero Pi refs)
- [x] `assets/chains/sdd-full.chain.md` — available via vendor (zero Pi refs)
- [x] `assets/chains/sdd-plan.chain.md` — available via vendor (zero Pi refs)
- [x] `assets/chains/sdd-verify.chain.md` — available via vendor (zero Pi refs)
- [x] Update `user-prompt-submit.sh` to lazy-load from `vendor/gentle-pi/assets/`:
      `inject_asset_manifest()` emits a path manifest per prompt (not file content).
      Agents read the asset file when the workflow applies — nothing is preloaded eagerly.
      orchestrator.md excluded (Pi-specific); sub-assets and chains are platform-agnostic.

### Phase 8 — Cleanup Pass ✅
Executed after full live flow validation (all 47 bats tests green, hooks verified manually).

**Bug fixed before cleanup:**
- `inject_adapter_skills()` table formatting: `$()` strips trailing newlines from `plugin_rows`/`vendor_rows`,
  causing rows to concatenate into a single line. Fixed printf format to `'%s%s\n%s\n%s\n'` with explicit `\n`
  separators. Committed as `fix(hook): preserve row separators in adapter skills table`.

**Files removed (Python era leftovers, no longer applicable):**
- `plugin/claude-code/pytest.ini` — pytest config; all tests now run under bats
- `plugin/claude-code/requirements-dev.txt` — `pytest>=7.0`; replaced by `tests/install-deps.sh`

**Files updated:**
- `plugin/claude-code/.env.example` — Usage line updated from `python scripts/session-start.py`
  to `bash scripts/session-start.sh`; env var documentation itself remains valid

**Untracked artifacts (already gitignored, no action needed):**
- `plugin/claude-code/scripts/__pycache__/` — Python bytecode, covered by `__pycache__/` in `.gitignore`
- `plugin/claude-code/tests/__pycache__/` — same
- `.pytest_cache/` — covered by `.pytest_cache/` in `.gitignore`
- `md/MIGRATION.MD` — covered by `/md` in `.gitignore`

---

## Ecosystem Position

```
Claude Code
    └── gentle-claude     ← this repo (workflow discipline + review gates)
    └── engram plugin     ← persistent memory (separate, already exists)

Pi
    └── gentle-pi         ← npm:gentle-pi (same role, mature reference)
    └── gentle-engram     ← npm:gentle-engram (memory)
```

gentle-claude is the Claude Code counterpart of gentle-pi.
The goal is feature parity with gentle-pi's core adapter responsibilities.
