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

5. **Satisfy the `release` gate**

   `gentle-ai review validate --gate release` demands five release-evidence inputs
   (`--release-configuration`, `--release-provenance`, `--release-generated`,
   `--release-publication-boundary`, `--release-evidence-freshness`) even though this repo has
   no build step, no npm package, and no CI-produced artifacts to attest to — publication here
   is exactly `git tag push -> release.yml -> GitHub Release`. The gate doesn't enforce a fixed
   schema on their contents (confirmed empirically: even `{}` for all five returns `allow`), so
   feed it minimal, honest JSON describing that reality instead of fabricating build/CI data
   that doesn't exist:

   ```bash
   TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)
   SHA=$(git rev-parse HEAD)
   TAG="v<x.y.z>"
   DIR=$(mktemp -d)

   echo '{"release_type":"tag-push-github-release","build_step":"none","package_registry":"none","workflow":".github/workflows/release.yml"}' \
     > "$DIR/configuration.json"
   echo "{\"vcs\":\"git\",\"commit\":\"$SHA\",\"tag\":\"$TAG\",\"source_repo\":\"https://github.com/Manuelcarbajal/gentle-harnesses\",\"built_from\":\"tagged source tree, no build step\"}" \
     > "$DIR/provenance.json"
   echo '{"generated_artifacts":[]}' > "$DIR/generated.json"
   echo '{"publication_targets":["github_release"],"sealed_by":"release.yml (softprops/action-gh-release) on tag push","npm":"not_published"}' \
     > "$DIR/publication-boundary.json"
   echo "{\"checked_at\":\"$TS\",\"sources\":[\"gentle-ai review finalize evidence\",\"full bats suite run\"]}" \
     > "$DIR/evidence-freshness.json"

   gentle-ai review validate --gate release --cwd . --lineage <lineage_id> \
     --release-configuration "$DIR/configuration.json" \
     --release-provenance "$DIR/provenance.json" \
     --release-generated "$DIR/generated.json" \
     --release-publication-boundary "$DIR/publication-boundary.json" \
     --release-evidence-freshness "$DIR/evidence-freshness.json"
   ```

   `<lineage_id>` is the review transaction already validated at `pre-commit`/`pre-push` for
   this release commit (printed by `gentle-ai review start`/`review status`). This must return
   `"result": "allow"` before tagging — if it doesn't, stop and investigate, do not tag on a
   denied gate.

6. **Tag and push the tag**

   ```bash
   git tag -a v<x.y.z> -m "gentle-claude v<x.y.z>"
   git push origin v<x.y.z>
   ```

   Pushing the tag is what triggers `release.yml` — there is no manual `gh workflow run` step.

7. **Verify the release**

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
- `release` gate result (`allow`, or the denial reason if you stopped instead of tagging).
- Tag pushed (`v<x.y.z>`).
- `release.yml` run URL and conclusion.
- GitHub Release URL.
