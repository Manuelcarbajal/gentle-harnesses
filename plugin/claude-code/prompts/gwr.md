# gwr — Wrap Up

Execute in strict order:

1. **Changelog**: add or update `## [Unreleased]` following the repo's existing changelog conventions. Include all user-facing changes made this session.
2. **Comment**: if the work ties to an issue or PR and no final comment was posted this session, draft and post exactly one wrap-up comment. Skip for work not tied to an issue or PR.
3. **Stage**: stage only files modified during the current session. Do not use `git add .` or `git add -A`.
4. **Commit**: use a conventional commit message. If the work closes a single issue, include `closes #<number>`. If multiple issues are closed, ask for clarification before committing. If no issue, omit references.
5. **Branch check**: if not on `main`, stop here and require explicit user confirmation before pushing.
6. **Push**: push the current branch to remote.

Do NOT create a PR unless explicitly requested after this completes.
