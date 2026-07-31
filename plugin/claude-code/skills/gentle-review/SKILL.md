---
description: "Run a gentle-ai review from the main thread in Claude Code (no review-* subagents). Trigger: review, gentle-review, review gate, capture-result, review a change before commit/release."
---

# gentle-review (Claude Code native review)

Drive the gentle-ai negotiated review lifecycle **entirely from the main thread**, which has full
`Bash`. This is the supported Claude Code path — it does NOT dispatch the `review-*` lens subagents.

**Why this exists**: the OpenCode 4-lens-on-frozen-trees *subagent* protocol cannot run in Claude
Code. The `review-*` agents have no `Bash` (can't run the mandated `git diff`/`cat-file` inspection)
and Claude Code has no seam to inject the frozen trees INTO a subagent (`UserPromptSubmit`
additionalContext reaches only the main thread; there is no pre-subagent inject). So the reviewer
work happens here, in the orchestrator thread, and results are submitted through the binary's
**additive headless capability**: `gentle-ai review capture-result`. This is a sanctioned CLI path,
not a workaround.

## When to use

- **Routine review before commit/push/release** → use this Skill.
- **High-risk change** (auth, security boundaries, the review gate itself, releases, or anything
  where confirmation bias is dangerous) → run this Skill AND `judgment-day`. This Skill keeps the
  frozen-tree byte-exact inspection but is a single actor reviewing — it has no blind adversarial
  separation. `judgment-day` (two blind judges) supplies that and works natively in Claude Code
  because its judges read files directly and do not depend on the frozen-tree contract.

## Hard rules

- Route **only** from the native `next_transition`. Never route from status prose, lifecycle
  state, or your own tier guess. Never call `review start` reactively to satisfy a gate — gates
  read receipts via `review status`.
- Never fabricate a `capture-result`. If the main-thread inspection cannot read the frozen trees,
  submit `inspection.status: incomplete` honestly and stop — an incomplete result is never a PASS.
- Do the inspection against the **frozen trees** from START (`base_tree`/`candidate_tree`), never
  the live worktree, index, or HEAD.

## Procedure

### 1. Ask the facade for the next transition

```bash
gentle-ai review status --cwd . --contract gentle-ai.review-integration/v2 --next-transition true
```

Read only `next_transition`:
- `execute` → run its exact operation with its exact argument tokens.
- `collect` → satisfy only its named inputs with their exact capture operations, then query status again.
- `stop` → stop and surface its `reason_code`; run no lifecycle operation.

A clean tree has no candidate and fails safely — there is nothing to review; that is not an error to work around.

### 2. Start (only when the transition names `review.start`)

```bash
gentle-ai review start --cwd . --contract gentle-ai.review-integration/v2 --locale es
```

- START freezes the candidate and derives tier → lenses (0 for low risk, 1 focus lens for standard,
  canonical 4R for high) and the correction budget `min(200, ceil(changed_lines/2))`.
- Add `--focus <risk|resilience|readability|reliability>` only if you must pin the standard-risk lens.
- **Consent**: if START returns the typed `consent/v2` blocking envelope, present it to the user
  faithfully and once, in Spanish (`--locale es` already asks for the Spanish envelope): headline,
  reason, value as concrete benefits, every effect as concrete consequences, and the off-path note —
  preserve order, selection mode, and the exact answer tokens (`granted`/`declined`). Then re-run
  START with `--consent granted` or `--consent declined` for the user's answer. Never answer for them.
  A decline is scoped to this candidate; it is not the kill switch.
- Before a canonical 4R run, give the one cost/side-effect forecast (4 lens inspections + the
  frozen budget + at most one bounded correction) once, not per lens.

### 3. Per lens — inspect in the main thread, then capture

For each lens the transition names, do NOT spawn a subagent. Inspect the frozen trees here, then
submit the result. Run `gentle-ai review schema reviewer` once to get the exact result shape and a
working example.

**Read-only frozen-tree inspection** (main thread Bash; `<base>`/`<cand>` are the START tree ids):

```bash
env -i PATH="$PATH" LC_ALL=C GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL=/dev/null GIT_ATTR_NOSYSTEM=1 \
  git --no-replace-objects --no-pager -c color.ui=false -c core.attributesFile=/dev/null -c diff.external= \
  diff --name-status --text --no-ext-diff --no-textconv --no-renames --ignore-submodules=none <base> <cand> --
# then, per changed path, the selective patch/bytes:
env -i PATH="$PATH" LC_ALL=C GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL=/dev/null GIT_ATTR_NOSYSTEM=1 \
  git --no-replace-objects --no-pager -c color.ui=false -c core.attributesFile=/dev/null -c diff.external= \
  diff --patch --text --full-index --no-color --no-renames --no-ext-diff --no-textconv \
  --diff-algorithm=myers --no-indent-heuristic --unified=3 --ignore-submodules=none <base> <cand> -- ':(literal)<path>'
env -i PATH="$PATH" LC_ALL=C GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL=/dev/null GIT_ATTR_NOSYSTEM=1 \
  git --no-replace-objects --no-pager cat-file -p '<tree>:<path>'
```

**Lens scope** (inspect only what the named lens owns):
- `risk` — security, authorization, data exposure/loss, unsafe input, secrets, dependency vulns.
- `resilience` — fallbacks, retry/backoff, graceful degradation, observability, rollback, SLO risk.
- `readability` — naming, complexity, intention, maintainability, review size, context clarity.
- `reliability` — behavior-first tests, coverage value, edge cases, determinism, contracts, regressions.

**Candidate-causal admission**: report only real user-impacting defects introduced/activated/worsened
by this candidate. BLOCKER/CRITICAL need changed-hunk / created-path / differential-test / before-after
proof. Unchanged defects are pre-existing (a follow-up, not a blocker); unproved causality is unknown.
Style or suspicion is not a finding.

**Submit** the result JSON (shape from `schema reviewer`: `subject_hash`, `inspection{status,paths}`,
`findings[]`, `evidence[]` with at least one non-placeholder entry) via the headless capture:

```bash
gentle-ai review capture-result --cwd . \
  --lineage <lineage_from_start> --lens <lens> --order <zero_based_order> \
  --expected-revision <expected_revision> --subject-hash <subject_hash> \
  --input result.json
```

Use `--preflight true` first to verify the binding without persisting, if you want to check it before writing.

### 4. Loop to the terminal gate

Re-query status and follow each returned transition: a `collect` for `correction_lines` (only within
the frozen budget, at most one bounded correction — forecast before editing, then run the one named
read-only fix validator it asks for), then onward until the returned `review.validate` allows the
terminal gate. Do not loop-until-clean; one immutable candidate permits at most one scoped correction.

### 5. The gate plugs into the existing hook

`plugin/claude-code/scripts/pre-tool-use.sh` already validates the receipt on `git commit`/`git push`
(and `release` on tag). Once the lifecycle reaches an allowed receipt, those gates pass — no extra
wiring. Do not commit on a denied or incomplete gate.

## Output contract

Report:
- Lineage id and derived tier/lenses/correction budget from START.
- Per lens: `inspection.status` and finding count (0 if clean), never an incomplete result dressed up as a pass.
- Terminal `review.validate` result (`allow`, or the denial reason if you stopped).
- Whether `judgment-day` was also run (required for high-risk changes).
