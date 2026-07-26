# gpr — PR Review

1. Apply `inprogress` label: `gh pr edit <number> --add-label inprogress`. Report failure but continue.
2. Read the full PR: description, all comments, all commits, and the diff (`gh pr view`, `gh pr diff`).
3. Read every linked issue referenced in the PR body or comments (find `#<number>` refs).
4. Independently verify behavior — do not accept the PR author's analysis at face value. Trace execution paths in code.
5. Check changelog: verify an entry exists for this PR in `## [Unreleased]`. Flag if missing or in the wrong section.
6. Check docs: flag if a feature or API change has no corresponding README or reference update.
7. Output structured review:
   - **Good**: improvements and strengths
   - **Bad**: bugs, missing tests, regressions, risks
   - **Ugly**: subtle or high-impact problems that may be missed on first read
   - **Questions**: clarifications needed before merge

Do NOT auto-approve. Do NOT post the review as a GitHub comment unless explicitly asked.
