---
name: project-ai-audit
description: Audit whether a single repository actually meets AI collaboration governance expectations after initialization. Use when you need to review a repository for audit readiness, document quality, task traceability, testing evidence, and meaningful commit guidance.
---

# Project AI Audit

Use this skill after initialization or when a repository claims to already support AI-assisted development.

## Workflow

1. Build the smallest useful context.
- Read `AGENTS.md`, `README.md`, `TESTING.md`, and the docs listed in README navigation.
- Read a few recent task docs if `docs/tasks/` or similar directories exist.
- Read package or build files only when needed to verify commands.

2. Run the audit check.
- Execute `scripts/audit_ai_project.sh <repo-root>`.
- Use the script as the baseline report, not the final conclusion.

3. Review effectiveness, not just existence.
- Check whether task templates have been used in real task records.
- Check whether testing docs match actual commands.
- Check whether docs navigation and AGENTS index are internally consistent.
- Check whether commit guidance explains how to keep output meaningful for team metrics.

4. Report findings with severity.
- Prioritize gaps that would fail management review or make contribution metrics misleading.
- Distinguish missing artifacts, stale docs, and low-trust evidence.

5. Recommend the next action.
- If baseline artifacts are missing, send the user to `$project-ai-init`.
- If the repo is structurally fine but unmanaged across many projects, send the user to `$gitlab-project-triage`.

## Language

- Audit findings, governance summaries, and repository collaboration docs should default to Chinese.
- Keep commands, paths, code identifiers, and Conventional Commit types in English.
- When reviewing an English API-facing README, do not force translation of existing external-facing technical content.

## Audit Focus

- AI workflow can be reconstructed from repository evidence.
- Plan, review, testing, retest, and delivery records have a documented home.
- README and AGENTS point reviewers to the right docs.
- Testing and validation instructions are plausible for the actual project stack.
- Commit guidance helps distinguish meaningful output from noisy churn.

## Resources

- `scripts/audit_ai_project.sh`
- `references/audit-checklist.md`
