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

**Señales de riesgo alto (paths):**
- Frases: `data-exposure`, `data-loss`, `privilege-escalation`
- Tokens: `auth`, `security`, `payments`, `permissions`, `shell`, `secrets`, `credentials`, `tokens`, `update`

**Para MEDIUM — lens dominante (orden de prioridad):**
```
risk > resilience > reliability > readability
```

**Budget de corrección:** `min(200, ceil(originalChangedLines / 2))`

**Lo que esto significa para gentle-claude:**
El hook `pre-tool-use.py` actualmente bloquea en git commit/push sin discriminar el tamaño
ni el riesgo del cambio. Con este modelo, podría evaluar el diff antes de decidir si pedir
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
| SessionStart compact (post-compaction) | ✅ | ❌ | A |
| UserPromptSubmit | ✅ | ✅ | A |
| SubagentStop | ✅ | ❌ | A |
| Stop (async) | ✅ async | ✅ sync | A |

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

Lo que gentle-claude necesita implementar (responsabilidad A, actualmente ausente):

1. `marketplace.json` — **crítico**, sin esto no existe en el marketplace
2. Binary local — **crítico**, elimina el mayor punto de falla en instalación
3. post-compaction hook — **importante**, recupera contexto perdido
4. SubagentStop hook — **importante**, captura pasiva de memoria
5. Risk-based lens routing — **importante**, ahorra tokens en cambios triviales
6. Safety guards completos — **medio**, actualmente solo bloquea git
7. Orchestrator assets separados — **medio**, mejor mantenibilidad que un CLAUDE.md monolítico
8. Chains — **medio**, shortcuts de workflow
9. `release` skill — **bajo**, faltante en el catálogo
10. Startup banner — **bajo**, polish
11. Model routing — **bajo**, conveniencia

---

## Migration Checklist

### Phase 0 — Foundations (do first)
- [ ] Create `.claude-plugin/marketplace.json`
- [ ] Tag v0.1.0 in git + create GitHub Release
- [ ] Add GitHub Topics: `gentle-ai`, `claude-code`, `plugin`, `review-lifecycle`, `skill-registry`
- [ ] Write `CHANGELOG.md`

### Phase 1 — Structure
- [ ] Move plugin files under `plugin/claude-code/`
- [ ] Keep root as project metadata (README, LICENSE, CONTRIBUTING, etc.)
- [ ] Update `hooks/hooks.json` paths accordingly

### Phase 2 — Binary
- [ ] Add `scripts/gentle-ai-binary.sh` — local binary resolution with fallback to PATH
- [ ] Document binary version pinning strategy

### Phase 3 — Missing Hooks
- [ ] Add `post-compaction.sh` (SessionStart compact matcher)
- [ ] Add `subagent-stop.sh` (SubagentStop hook)
- [ ] Make `session-stop.sh` async (non-blocking)

### Phase 4 — Scripts Migration
- [ ] Migrate `session-start.py` → `session-start.sh`
- [ ] Migrate `user-prompt-submit.py` → `user-prompt-submit.sh`
- [ ] Migrate `pre-tool-use.py` → `pre-tool-use.sh`
- [ ] Migrate `session-stop.py` → `session-stop.sh`
- [ ] Rewrite test suite for shell scripts

### Phase 5 — CI/CD + Docs
- [ ] GitHub Actions: `test.yml` (pytest/bats on every PR)
- [ ] GitHub Actions: `release.yml` (tag → GitHub Release)
- [ ] Write `ARCHITECTURE.md`
- [ ] Write `DEVELOPMENT.md`
- [ ] Write `SECURITY.md`
- [ ] Write `ROADMAP.md`

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
