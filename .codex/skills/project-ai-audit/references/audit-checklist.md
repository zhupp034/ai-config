# Audit Checklist

Use this checklist when reviewing a repository for AI collaboration governance.

## Language
- Audit output defaults to Chinese for internal collaboration summaries.
- Commands, paths, code ids, and commit types stay in English.

## Required outcomes
- A reviewer can find baseline docs from README or AGENTS.
- The repository defines where task plans, reviews, tests, retests, and delivery reports live.
- The defined commands and validation steps appear credible for the actual stack.
- The repository explains how to keep Git output meaningful.

## Common failure patterns
- Docs exist but README has no navigation.
- Templates exist but there are no real task records.
- TESTING.md lists placeholder commands that do not match the repository.
- AGENTS.md talks about AI rules but not collaboration evidence.
- The repository has no rule for separating business changes from generated output or bulk formatting.

## Review output
- State overall status: ready, partial, or not ready.
- List findings in severity order.
- Separate initialization gaps from quality gaps.
- Recommend whether to use `$project-ai-init`, manual refinement, or `$gitlab-project-triage` next.
