---
name: task-delivery-workflow
description: Guide day-to-day feature or bug delivery so the work stays auditable for AI-assisted coding. Use when implementing a concrete task and you need help maintaining plan records, review checkpoints, testing evidence, retest notes, and final delivery reporting inside the repository.
---

# Task Delivery Workflow

Use this skill during actual task execution inside one repository.

## When to use

- The user is about to implement a feature, fix, refactor, or test change.
- The repository already has baseline AI docs or needs help following them.
- The goal is to keep a complete evidence chain while doing the work, not after the fact.

## Workflow

1. Read the repository guardrails.
- Read `AGENTS.md`, `TESTING.md`, and the task-related docs listed in README.
- If baseline docs are missing, recommend `$project-ai-init` first.

2. Create or update a task record before coding.
- Prefer a repository task directory such as `docs/tasks/`.
- Use `scripts/create_task_record.sh <repo-root> <task-slug>` to create a new task markdown when needed.
- Fill in at least plan, scope, reviewers, and initial validation strategy.

3. Keep the record updated while implementing.
- Add plan review notes when decisions change.
- Record implementation checkpoints, code review findings, and testing evidence.
- Record bugfix and retest notes instead of leaving them in chat only.

4. Close with a delivery summary.
- Make sure the task record contains user-visible changes, scope, validation, risks, and rollback notes when relevant.
- Reconcile the task record with the actual code and tests before final reporting.

## Language

- Task records, plan notes, review notes, test evidence summaries, and delivery reports should default to Chinese.
- Keep commands, paths, code symbols, test ids, and commit types in English.
- If the repository already has a Chinese governance style, stay consistent and do not mix in English prose unnecessarily.

## Rules

- Do not wait until the end to write evidence.
- Prefer repository-native evidence over private chat summaries.
- For user-facing changes, explicitly track loading, empty, error, and success validation.
- If no test was added, record the reason in the task doc.
- If the repository has no task template, create a minimal record rather than skipping documentation.

## Resources

- `scripts/create_task_record.sh`
- `references/task-record-guidance.md`
