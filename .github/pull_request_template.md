## What this PR does

<!-- One paragraph describing the change. Link to the related issue if any: Closes #N -->

## Review receipt

All changes must go through the gentle-ai review cycle before merging.

- [ ] `gentle-ai review start --cwd . --projection staged`
- [ ] All 4R lenses run (risk, resilience, readability, reliability)
- [ ] `gentle-ai review finalize --cwd . --lineage <id> --evidence <file>`
- [ ] `gentle-ai review validate --gate pre-commit --cwd .` → **allow**
- [ ] GGA pre-commit hook passed

## How the hook was tested

<!-- Describe how you verified the hook behaves correctly:
     - Unit tests added/updated (pytest)
     - Manual test with `claude --debug`
     - Edge cases covered -->

## Files changed

- [ ] `scripts/session-start.py`
- [ ] `scripts/user-prompt-submit.py`
- [ ] `scripts/pre-tool-use.py`
- [ ] `scripts/session-stop.py`
- [ ] `hooks/hooks.json`
- [ ] `.claude-plugin/plugin.json`
