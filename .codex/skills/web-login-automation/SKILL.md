---
name: web-login-automation
description: Log into an arbitrary website with account/password, then open a target page and continue browser automation. Use when the user wants to sign in to a specific web app, validate that login succeeded, or reuse the authenticated browser session for later actions.
---

# Web Login Automation

Use this skill for generic website login flows that rely on a browser form instead of a stable API.

This skill coordinates with [$playwright](/Users/zpp/.codex/skills/playwright/SKILL.md). Use that skill's wrapper script and browser session management rather than inventing a new browser driver.

## Required Inputs

Collect these values before automating:

- login page URL
- target page URL after login
- account value source
- password value source
- account input selector or a reliable way to identify it from a snapshot
- password input selector or a reliable way to identify it from a snapshot
- submit button selector or a reliable way to identify it from a snapshot

Also collect at least one success indicator:

- expected post-login URL pattern
- text that appears only after login
- element that exists only after login

## Workflow

1. Use the Playwright wrapper from the existing `playwright` skill.
2. Open the login page in a named session.
3. Snapshot the page and identify the account, password, and submit controls.
4. Fill credentials and submit.
5. Re-snapshot after navigation.
6. Verify the success indicator.
7. Open the target page in the same session if it is different from the landing page.
8. Continue the requested browser actions in the authenticated session.

## Recommended Session Naming

Use a stable session name derived from the site, such as:

- `zentao-login`
- `gitlab-login`
- `erp-login`

## Quick Start

```bash
export CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
export PWCLI="$CODEX_HOME/skills/playwright/scripts/playwright_cli.sh"

"$PWCLI" --session web-login open 'https://example.com/login' --headed
"$PWCLI" --session web-login snapshot
# Fill fields and click submit using refs from the snapshot.
"$PWCLI" --session web-login snapshot
"$PWCLI" --session web-login open 'https://example.com/app'
```

## Guardrails

- Do not assume selectors are stable across sites. Snapshot first unless the user explicitly provided tested selectors.
- Re-snapshot after submit, redirects, modals, MFA prompts, or SPA transitions.
- Treat credentials as user-provided secrets. Do not hardcode them into the skill.
- If the flow includes MFA, captcha, or SSO that requires human action, pause and ask the user to complete that step.
- If login succeeds and the user needs repeated follow-up actions, keep using the same Playwright session.

## Output

Report:

- whether login succeeded
- which session name was used
- the final page URL or page description
- any blockers such as captcha, MFA, or invalid credentials
