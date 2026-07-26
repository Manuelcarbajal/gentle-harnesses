# Development Guide

## Requirements

| Tool | Required | Purpose |
|---|---|---|
| bash | yes | hook scripts |
| jq | yes | JSON parsing in hooks |
| git | yes | submodule management |
| gentle-ai CLI | yes | review lifecycle, skill-registry |
| bats-core | dev only | test suite |
| codegraph | recommended | structural analysis in sessions |

## Clone

```bash
git clone --recurse-submodules https://github.com/Manuelcarbajal/gentle-ai-claude
cd gentle-ai-claude
```

If you cloned without `--recurse-submodules`:

```bash
git submodule update --init --recursive
```

## Run tests

Install bats dependencies (once):

```bash
bash plugin/claude-code/tests/install-deps.sh
```

Run the full suite:

```bash
bash plugin/claude-code/tests/run_bats.sh
```

Run a single file:

```bash
bash plugin/claude-code/tests/run_bats.sh plugin/claude-code/tests/bats/test_pre_tool_use.bats
```

Run with TAP output (for CI):

```bash
bash plugin/claude-code/tests/run_bats.sh --formatter tap
```

## Test structure

```
plugin/claude-code/tests/
  bats/
    helpers.bash              — shared setup: stub system, env vars, SCRIPTS_DIR
    test_pre_tool_use.bats    — classify_diff, classify_command, review gate
    test_user_prompt_submit.bats
    test_session_start.bats
    test_session_stop.bats
    test_post_compaction.bats
  libs/                       — bats-core, bats-assert, bats-support (gitignored)
  install-deps.sh             — clones bats libs on demand
  run_bats.sh                 — test runner
```

Each test file stubs external binaries (gentle-ai, git, codegraph, jq) via env vars
controlled by `helpers.bash`. No real binaries are called during tests.

## Update vendor/gentle-pi

Pull the latest skills, assets, and docs from gentle-pi:

```bash
git submodule update --remote vendor/gentle-pi
git add vendor/gentle-pi
git commit -m "chore(vendor): update gentle-pi to latest"
```

To pin to a specific commit:

```bash
cd vendor/gentle-pi
git checkout <commit-sha>
cd ../..
git add vendor/gentle-pi
git commit -m "chore(vendor): pin gentle-pi to <commit-sha>"
```

## Add a skill override

If a skill in `vendor/gentle-pi/skills/` needs a Claude Code-specific version:

1. Create `plugin/claude-code/skills/<skill-name>/SKILL.md`
2. The injection layer in `user-prompt-submit.sh` gives priority to plugin skills over
   same-named vendor skills automatically — no config needed.

## Expand vendor sparse checkout

To add a new directory from gentle-pi:

```bash
cd vendor/gentle-pi
git sparse-checkout add <directory>
cd ../..
git add vendor/gentle-pi
git commit -m "feat(vendor): add <directory> to sparse checkout"
```

Then update `inject_asset_manifest()` in `user-prompt-submit.sh` to include the new paths.

## Hook development

Hooks live in `plugin/claude-code/scripts/`. Shared utilities are in `gentle_ai.sh`.

To test a hook manually:

```bash
export CLAUDE_TOOL_NAME="Bash"
export CLAUDE_TOOL_INPUT='{"command":"git commit -m test"}'
export CLAUDE_PROJECT_DIR="/path/to/repo"
bash plugin/claude-code/scripts/pre-tool-use.sh
```

The hook exits with code `0` (allow) or `2` (block) and prints JSON to stdout.

## Release

1. Update `CHANGELOG.md` — move `[Unreleased]` entries under a new version section
2. Bump `version` in `.claude-plugin/plugin.json` (or wherever `plugin.json` lives)
3. Tag: `git tag v<version> && git push origin v<version>`
4. The `release.yml` GitHub Action publishes the release automatically
