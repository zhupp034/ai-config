---
name: meaningful-commit-coach
description: Help structure repository changes into meaningful Git commits that support productivity review. Use when changes are in progress or staged and you need help separating noisy churn from meaningful output, proposing commit boundaries, or drafting Conventional Commit messages.
---

# Meaningful Commit Coach

Use this skill before staging or committing changes in one repository.

## When to use

- The user asks how to split commits.
- The worktree contains mixed changes.
- The team cares about commit count and meaningful code metrics.
- You need Conventional Commit suggestions tied to actual work.

## Workflow

1. Inspect the current change set.
- Read `git status --short` and focused diffs.
- Group changes by intent: feature, fix, refactor, test, docs, generated output, dependency change.

2. Evaluate signal quality.
- Flag low-value churn such as broad formatting, unrelated edits, generated files, or mixed concerns.
- Explain why mixed commits weaken auditability and contribution metrics.

3. Propose commit boundaries.
- Use `scripts/suggest_commit_groups.sh <repo-root>` for a quick first pass.
- Refine manually when file-level grouping is not enough.
- Keep each suggested commit traceable to one main intent.

4. Draft commit messages.
- Use Conventional Commits.
- Prefer messages that reflect business or validation value, not generic file movement.

## Language

- Explanations and commit-splitting advice should default to Chinese.
- Keep suggested Conventional Commit messages, commands, paths, and code identifiers in English.

## Rules

- Never optimize for commit count alone.
- Separate generated assets, dependency upgrades, refactors, tests, and business behavior changes when practical.
- If the change set is too entangled, say so clearly and recommend restaging.
- Keep suggestions tied to current files, not abstract advice.

## Resources

- `scripts/suggest_commit_groups.sh`
- `references/commit-heuristics.md`
