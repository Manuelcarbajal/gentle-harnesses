---
description: gentle-claude release runbook — tag push to GitHub Release, no npm. Trigger: release, publish, version bump, tag, GitHub release.
---

# release (gentle-claude)

Release runbook for **this repo** (`gentle-harnesses` / `gentle-claude` plugin). This overrides
the vendored `vendor/gentle-pi/skills/release/SKILL.md`, which describes gentle-pi's npm release
process — that process does not apply here. gentle-claude has no npm package and no
`publish.yml` workflow.

## What release actually means here

`.github/workflows/release.yml` triggers on any pushed tag matching `v*`. It extracts the
matching `## [x.y.z]` section from `CHANGELOG.md` (falling back to `## [Unreleased]` if no exact
match) and creates a GitHub Release via `softprops/action-gh-release`. That's the entire release
mechanism: **tag push → GitHub Release**. There is no npm registry, no `publish.yml`, no
`dist-tag`, no package to verify with `npm view`.

## Release procedure

1. **Inspect state**

   ```bash
   git status --short
   git fetch origin main --tags
   git log --oneline --decorate --max-count=5 origin/main
   ```

2. **Update the changelog**

   - Move the relevant `[Unreleased]` entries into a new `## [x.y.z] - YYYY-MM-DD` section in
     `CHANGELOG.md`, following [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
   - The version in that heading must exactly match the tag you push (`v0.2.0` → `## [0.2.0]`),
     or the workflow falls back to the `Unreleased` section instead.

3. **Bump the version**

   - Update `version` in `plugin/claude-code/.claude-plugin/plugin.json` to match.

4. **Commit and push**

   ```bash
   git add CHANGELOG.md plugin/claude-code/.claude-plugin/plugin.json
   git commit -m "chore(release): bump version to <x.y.z>"
   git push origin main
   ```

5. **Tag and push the tag**

   ```bash
   git tag -a v<x.y.z> -m "gentle-claude v<x.y.z>"
   git push origin v<x.y.z>
   ```

   Pushing the tag is what triggers `release.yml` — there is no manual `gh workflow run` step.

6. **Verify the release**

   ```bash
   gh run list --repo Manuelcarbajal/gentle-harnesses --workflow release.yml --limit 3
   gh release view v<x.y.z> --repo Manuelcarbajal/gentle-harnesses
   ```

## Hard rules

- Never run gentle-pi's npm release steps (`pnpm publish`, `gh workflow run publish.yml`) against
  this repo — there is no such workflow here and no npm package to publish.
- Never push a tag whose version doesn't have a matching `CHANGELOG.md` section — the release
  notes will silently fall back to `Unreleased`, which may not describe that version.
- Follow the same release-gate discipline as any other push to `main`: this repo's review
  lifecycle (`gentle-ai review validate --gate release`) still applies before tagging.

## Output contract

Report:

- Commit SHA pushed to `main`.
- Tag pushed (`v<x.y.z>`).
- `release.yml` run URL and conclusion.
- GitHub Release URL.
