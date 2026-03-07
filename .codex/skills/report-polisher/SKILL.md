---
name: report-polisher
description: Polish structured report drafts into concise, natural Chinese Markdown using shared semantic rules. Use when the user asks to润色周报、月报、日报、总结、述职草稿，or when another skill has already produced a draft and only wording cleanup is needed.
---

# Report Polisher

## Overview

Use this skill when the source content already exists and the remaining work is semantic rewriting, de-duplication, and Markdown-preserving polish.
Prefer the shared rules in `/Users/zpp/.codex/memories/report-polish-rules.md` and keep terminology aligned with `/Users/zpp/.codex/memories/term-glossary.json`.

## Workflow

1. Read the shared polish rules from `/Users/zpp/.codex/memories/report-polish-rules.md`.
2. Keep the original Markdown structure unless the user explicitly asks to restructure it.
3. Preserve facts, dates, names, versions, and technical identifiers.
4. Rewrite commit-like, mixed-language, or工单风格内容 into natural Chinese that reads like an actual report.
5. Prefer report semantics over string replacement: merge repetitive fragments, smooth conjunctions, and make long bullets readable.
6. Use the weekly rules for 周报 and the monthly rules for 月报.

## Input Contract

1. The input should be an existing Markdown draft, not raw scattered notes.
2. The user or calling skill should indicate the mode when it is clear: `weekly_frontend`, `monthly_frontend`, or `daily_frontend`.
3. If the mode is not stated, infer it from the document structure and wording, but say which mode you used when ambiguity matters.
4. Keep headings, list structure, dates, and section order unless the user explicitly asks for restructuring.

## Output Contract

1. Output only the polished Markdown unless the user explicitly asks for commentary.
2. Preserve the original structure and section hierarchy.
3. Do not invent missing sections, achievements, risks, or plans.
4. If the draft is already clean, make only minimal edits.
5. For frontend reports, keep the output technically grounded and readable by both peers and managers.

## Modes

1. `weekly_frontend`: Weekly report for a frontend developer. Prioritize concrete delivery, fixes, engineering optimization, risks, and next steps.
2. `monthly_frontend`: Monthly report for a frontend developer. Prioritize phase-level progress, recurring engineering themes, and collaboration outcomes.
3. `daily_frontend`: Daily report for a frontend developer. Preserve same-day granularity and avoid over-aggregation.

## Standard Prompt

Recommended invocation template:

```text
Use $report-polisher in <mode> to polish this frontend report draft.
Keep the Markdown structure unchanged.
Preserve all supported facts, dates, names, versions, and technical identifiers.
Rewrite it into concise, natural Chinese that matches an experienced frontend developer's writing style.
```

## Resources

- `/Users/zpp/.codex/memories/report-polish-rules.md`: Shared semantic rule source for AI polishing.
- `/Users/zpp/.codex/memories/term-glossary.json`: Shared terminology mapping for stable project/module naming.
