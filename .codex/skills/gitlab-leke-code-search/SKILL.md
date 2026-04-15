---
name: gitlab-leke-code-search
description: Use when you need to locate which repository, file, route, or implementation in gitlab.leke.cn corresponds to a URL, page path, route fragment, keyword, API name, component name, or error text. Supports local-first search and authenticated GitLab follow-up when local evidence is insufficient.
---

# GitLab Leke Code Search

Use this skill to answer questions like:

- “这个 URL 对应哪个项目/页面？”
- “这个路由在哪个仓库实现？”
- “这个接口、关键词、报错在哪个仓库里？”
- “帮我在 gitlab.leke.cn 上找实现位置”

This skill is for locating code ownership and implementation paths, not for making code changes.

## Core Workflow

1. Normalize the target.
- Extract the most searchable signals from the user input.
- Prefer stable tokens such as route fragments, file names, query params, API paths, component names, domain names, and error strings.
- For URLs, split into:
  - host
  - pathname
  - important query params
  - obvious business nouns

2. Search the current local repository first.
- Check `git remote -v`.
- Use `rg` on the current repo for the strongest tokens.
- Look for route definitions, jump/link builders, controller mappings, and page/component names.
- If the current repo already proves the answer, stop there.

3. Search local GitLab workspaces next.
- If the current repo is insufficient, search likely local workspace roots such as `/Users/.../gitlab`.
- Prefer `rg` over broad filesystem walking.
- Search for the exact route fragment first, then broader nouns.
- When searching many repos, prioritize likely names rather than scanning everything blindly.

4. Infer candidate repositories before touching GitLab.
- Use naming clues from the URL or code:
  - `/page/repository/...` often points to frontend SSR or webapp routing repos
  - `auth/common/workbook/...` often points to question/workbook backend repos
  - `index.html#/...` often points to SPA frontend repos
- Check whether the current repo references another service or domain in jump URLs.
- Build a short candidate list and test those first.

5. Use GitLab only when local evidence is insufficient or stale.
- If the user provided GitLab credentials, you may use them.
- If local secrets exist, prefer reading them from `~/.codex/secrets/common.env` before asking the user again.
- Prefer repository-level verification via `git ls-remote` and shallow clone over relying on GitLab UI search alone.
- Good pattern:
  - `git ls-remote https://<user>:<pass>@gitlab.leke.cn/<group>/<repo>.git`
  - `git clone --depth 1 ... /tmp/<repo>`
  - `rg -n "token1|token2" /tmp/<repo>`
- Use temporary clone paths under `/tmp`.

6. Use browser login only when it materially helps.
- If GitLab UI context is needed, use `$web-login-automation` and `$playwright`.
- Login flow should be:
  - open `https://gitlab.leke.cn/users/sign_in`
  - fill credentials
  - verify login success
  - use search or inspect repository pages
- Do not rely on GitLab global search as the only source of truth for code search. It is often weaker than shallow clone plus `rg`.

7. Report the result as evidence, not guesswork.
- Always return:
  - repository name/path
  - matched file path(s)
  - why they match
  - whether this is a direct implementation, a route entry, or only a caller/jump source
- If confidence is partial, say so explicitly.

## Search Order

Use this order unless the user explicitly asks for GitLab-first:

1. Current repo
2. Nearby local GitLab repos
3. Candidate repo verification with `git ls-remote`
4. Shallow clone candidate repos to `/tmp`
5. GitLab browser login and UI inspection if still needed

## Query Construction

For URLs, try queries in this order:

1. Exact route fragment
- Example: `resourcedetails/workbook`

2. Route + key param name
- Example: `workbookId`

3. Page/component guess
- Example: `ResourceDetails/workbook`

4. Link builder patterns
- Example: `/page/repository/resourcedetails/workbook`

5. Business noun only
- Example: `workbook`

For APIs and backend paths, try:

1. Exact endpoint path
2. Final path segment
3. Controller/action naming variants
4. Related model or service names

## Heuristics

- A local backend repo may only generate a jump URL, while the real page lives in another frontend repo.
- A frontend SSR repo often contains:
  - route registration
  - page component entry
  - URL builder helpers
- A business backend repo often contains:
  - controller mappings
  - JSON/data endpoints
  - service and model code
- When one repo references another domain in `viewUrl`, `jump.ts`, `business.ts`, or controller redirects, follow that clue.

Read `references/search-playbook.md` for concrete patterns and repository clues.

## Credentials and Safety

- Treat user-provided GitLab credentials as secrets.
- Use them only for the current search task.
- When available locally, read credentials from `~/.codex/secrets/common.env`.
- Prefer environment-style keys such as `GITLAB_LEKE_USERNAME` and `GITLAB_LEKE_PASSWORD`.
- Do not write credentials into skill files, scripts, committed code, or summaries.
- Avoid printing raw credentialed URLs back to the user.

## Output Format

Default to Chinese and keep it concise.

Good output should include:

- `仓库`：GitLab 仓库路径
- `命中文件`：1-3 个最关键文件
- `定位结论`：这是入口路由、页面实现，还是跳转来源
- `证据`：哪一行或哪段文字证明了结论
- `不确定性`：如果只是候选结论，要明确说明

## When Not to Use

- The user only wants to modify the current repository and the target is already known.
- The user is asking for generic GitLab usage help rather than locating code.
- The task is to review or implement code, not to find where it lives.
