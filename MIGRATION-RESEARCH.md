# Migration Research

Status: **COMPLETE — ready to plan migration**

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
| Risk-based lens routing (LOW/MED/HIGH) | ✅ `lib/review-risk.ts` | ❌ siempre bloquea igual | A |
| 0 lenses para cambios triviales | ✅ | ❌ | A |
| 1 lens para cambios estándar | ✅ | ❌ | A |
| 4R completo para high-risk / >400 líneas | ✅ | ❌ parcial | A |
| Correction budget `min(200, ceil(lines/2))` | ✅ | ❌ | GA |
| Native authority binding | ✅ | ✅ vía gentle-ai CLI | GA |

### Safety guards

| Feature | gentle-pi | gentle-claude | Responsabilidad |
|---|---|---|---|
| Clasificación de comandos (allow/confirm/block) | ✅ `classifyGuardedCommand()` | ❌ solo git commit/push | A |
| Hard-deny para comandos destructivos | ✅ | ❌ | A |
| Confirm para operaciones sensibles | ✅ | ❌ | A |

### Orchestrator assets

| Feature | gentle-pi | gentle-claude | Responsabilidad |
|---|---|---|---|
| `assets/orchestrator.md` | ✅ | ❌ todo en CLAUDE.md | A |
| `assets/orchestrator-skills.md` | ✅ | ❌ | A |
| `assets/orchestrator-memory.md` | ✅ | ❌ | A |
| `assets/orchestrator-delegation.md` | ✅ | ❌ | A |
| `assets/sdd-orchestrator-workflow.md` | ✅ | ✅ en `~/.claude/skills/` | A |

### Chains (workflow shortcuts)

| Feature | gentle-pi | gentle-claude | Responsabilidad |
|---|---|---|---|
| `4r-review.chain.md` | ✅ | ❌ | A |
| `sdd-full.chain.md` | ✅ | ❌ | A |
| `sdd-plan.chain.md` | ✅ | ❌ | A |
| `sdd-verify.chain.md` | ✅ | ❌ | A |

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
| release | ✅ | ❌ | A |
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
2. ❌ Binary local-first en `gentle_ai_bin()` — crítico, `$CLAUDE_PLUGIN_ROOT/bin/` antes de PATH
3. ✅ post-compaction hook — importante
4. ✅ SubagentStop hook — importante
5. ❌ Risk-based lens routing en `pre-tool-use.sh` — importante, LOW/MED/HIGH
6. ❌ Safety guards completos — medio, actualmente solo bloquea git commit/push
7. ❌ `skills/gentle-ai/SKILL.md` — **importante**, define la identidad del harness como skill
      inyectable; mayor impacto en token efficiency que cualquier otra optimización
8. ❌ Prompts operacionales (`gpr`, `gcl`, `gis`, `gwr`) — importante, workflows específicos
      con gentle-ai para PR review, changelog, issues — actualmente no existen
9. ❌ Orchestrator assets separados — medio, `assets/` con lazy-loading vs CLAUDE.md monolítico
10. ❌ Chains — medio, `4r-review`, `sdd-full`, `sdd-plan`, `sdd-verify`
11. ❌ `release` skill — bajo
12. ❌ Startup banner — bajo, polish (no equivalente nativo en Claude Code)
13. ❌ Model routing — bajo, conveniencia

---

## Migration Checklist

### Phase 0 — Foundations ✅
- [x] Create `.claude-plugin/marketplace.json`
- [x] Tag v0.1.0 in git + create GitHub Release
- [ ] Add GitHub Topics: `gentle-ai`, `claude-code`, `plugin`, `review-lifecycle`, `skill-registry`
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

### Phase 5 — CI/CD + Docs ❌
- [ ] GitHub Actions: `ci.yml` (bats + pytest on every PR, matching gentle-pi's `pnpm test` pattern)
- [ ] GitHub Actions: `release.yml` (tag → GitHub Release, mirrors gentle-pi's `publish.yml`)
- [ ] Write `ARCHITECTURE.md`
- [ ] Write `DEVELOPMENT.md`
- [ ] Write `SECURITY.md`
- [ ] Write `ROADMAP.md`
- [ ] Write `CHANGELOG.md`

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

Sparse checkout — only materializes the 3 directories applicable to Claude Code:
  `vendor/gentle-pi/skills/`, `vendor/gentle-pi/prompts/`, `vendor/gentle-pi/contracts/`

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
      with sparse checkout: `git sparse-checkout set skills prompts contracts`
- [ ] Register `vendor/gentle-pi/skills/` as a skill source in `gentle-ai skill-registry` config
      so the registry discovers vendor skills automatically on session start — this unlocks
      `release`, `cognitive-doc-design`, and `comment-writer` without any local copies
- [ ] Document in `DEVELOPMENT.md`: `git submodule update --remote` to pull latest gentle-pi

### Phase 7 — Orchestrator Assets & Chains ❌
Reduces CLAUDE.md bloat via modular lazy-loading. Mirrors `assets/` structure in gentle-pi.

- [ ] Create `assets/orchestrator.md` — thin harness layer with lazy-load pointers to other assets
- [ ] Create `assets/orchestrator-delegation.md` — routing table + mandatory delegation triggers
- [ ] Create `assets/orchestrator-memory.md` — engram lifecycle + SDD artifact keys per phase
- [ ] Create `assets/orchestrator-skills.md` — skill discovery + registry protocol
- [ ] Create `assets/chains/4r-review.chain.md`
- [ ] Create `assets/chains/sdd-full.chain.md`
- [ ] Create `assets/chains/sdd-plan.chain.md`
- [ ] Create `assets/chains/sdd-verify.chain.md`
- [ ] Update `user-prompt-submit.sh` to inject modular orchestrator assets instead of
      relying on monolithic CLAUDE.md

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
