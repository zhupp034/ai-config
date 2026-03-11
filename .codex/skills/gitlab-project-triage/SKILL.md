---
name: gitlab-project-triage
description: Triage and prioritize many local GitLab repositories for AI governance rollout. Use when you need to scan a parent directory of repositories, classify projects into priority tiers, and recommend which repositories should receive AI init or audit work first.
---

# GitLab Project Triage

Use this skill for multi-repository governance, not for changing a single repository.

## Workflow

1. Confirm the root directory that contains repositories.
- Prefer local GitLab workspace roots such as `/Users/.../gitlab`.
- Limit scanning depth to the repository layer.

2. Collect lightweight signals.
- Repository name
- Has `.git`
- Has `AGENTS.md`
- Has `README.md`
- Has active stack files such as `package.json`, `pyproject.toml`, `go.mod`
- Optional recent activity from local git history when needed

3. Run the triage script.
- Execute `scripts/triage_gitlab_projects.sh <root>`.
- Use the output as the first-pass classification.

4. Produce a rollout recommendation.
- P0: active repositories likely to be audited soon
- P1: maintained but lower priority repositories
- P2: legacy or dormant repositories
- Recommend whether each P0/P1 repo needs `$project-ai-init`, `$project-ai-audit`, or no action yet.

5. Keep the result pragmatic.
- Do not propose governance work for every repository at once.
- Default to a short list of highest-value repositories first.

## Language

- Triage summaries, priority explanations, and rollout suggestions should default to Chinese.
- Keep repository names, paths, commands, and next-action skill ids in English.

## Output expectations

- A concise table or list of P0, P1, and P2 repositories.
- Short reasons for each classification.
- Suggested next action per repository.

## Resources

- `scripts/triage_gitlab_projects.sh`
- `references/priority-rules.md`
