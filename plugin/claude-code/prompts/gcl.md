# gcl — Changelog Audit

1. Find the most recent release tag: `git describe --tags --abbrev=0`.
2. List all commits since that tag: `git log <tag>..HEAD --oneline`.
3. For each commit, determine if it has user-facing changes. Skip: doc-only changes, release housekeeping, and changelog updates themselves.
4. For each non-trivial commit, verify a matching entry exists in `## [Unreleased]` in the changelog.
5. Flag any commit with user-facing changes that has no changelog entry.
6. Flag changelog entries placed in the wrong section (e.g., a bug fix listed under Features).
7. Output:
   - If all entries are present: confirm the changelog is ready to release.
   - If entries are missing: list which commits need entries and propose the exact changelog text for each.
