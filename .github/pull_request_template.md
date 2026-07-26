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
     - Unit tests added/updated (bats)
     - Manual test with `claude --debug`
     - Edge cases covered -->

## Files changed

- [ ] `plugin/claude-code/scripts/session-start.sh`
- [ ] `plugin/claude-code/scripts/user-prompt-submit.sh`
- [ ] `plugin/claude-code/scripts/pre-tool-use.sh`
- [ ] `plugin/claude-code/scripts/post-compaction.sh`
- [ ] `plugin/claude-code/scripts/subagent-stop.sh`
- [ ] `plugin/claude-code/scripts/session-stop.sh`
- [ ] `plugin/claude-code/hooks/hooks.json`
- [ ] `plugin/claude-code/.claude-plugin/plugin.json`
- [ ] `.claude-plugin/marketplace.json`
