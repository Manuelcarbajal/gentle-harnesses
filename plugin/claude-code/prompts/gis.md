# gis — Issue Analysis

1. Apply `inprogress` label: `gh issue edit <number> --add-label inprogress`. Report failure but continue.
2. Read the full issue including ALL comments.
3. Read every linked issue or PR referenced in the thread (find `#<number>` refs).
4. Analyze by type:
   - **Bug**: ignore the author's suggested root cause. Trace the actual execution path in code. Find the real root cause. Propose a specific, targeted fix.
   - **Feature**: verify implementation suggestions against the actual codebase. Examine all relevant files. Recommend the most efficient implementation path. List every file that would change.
5. Output: analysis and proposal only.

Do NOT implement unless explicitly instructed after this analysis.
