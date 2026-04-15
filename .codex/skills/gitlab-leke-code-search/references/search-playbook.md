# Search Playbook

Use this file when the main skill is active and you need concrete lookup tactics.

## URL Reverse Lookup

Break a URL into:

- domain
- pathname
- query params
- resource nouns

Then search in this order:

1. Exact pathname fragment
2. Full jump URL pattern
3. Query parameter names
4. Resource noun + likely page type

Example:

- URL: `https://webapp.leke.cn/page/repository/resourcedetails/workbook?curScope=6&workbookId=2444`
- Search tokens:
  - `resourcedetails/workbook`
  - `/page/repository/resourcedetails/workbook`
  - `workbookId`
  - `ResourceDetails/workbook`

## Candidate Repository Clues

Common clues inside Leke repos:

- `ssr`, `page`, `routes`, `jump.ts`, `business.ts`
  - often frontend routing or page assembly repos
- `controller`, `@RequestMapping`, `details.htm`, `data.htm`
  - often backend MVC repos
- `viewUrl`, `window.open`, `redirect:`
  - often caller/jump sources, not the final implementation

## Fast Candidate Verification

When you suspect a repo path on GitLab:

1. Verify remote access:
```bash
git ls-remote https://<user>:<pass>@gitlab.leke.cn/<group>/<repo>.git | head
```

2. Shallow clone:
```bash
git clone --depth 1 https://<user>:<pass>@gitlab.leke.cn/<group>/<repo>.git /tmp/<repo>
```

3. Search inside:
```bash
rg -n "token1|token2|token3" /tmp/<repo>
```

## Reporting Rules

Classify findings explicitly:

- `直接实现`
  - route registration, page entry component, controller implementation
- `跳转来源`
  - link builder, jump helper, list item click handler
- `数据来源`
  - API endpoint, service, DAO, backend model
- `辅助证据`
  - docs, comments, tests, route maps

Prefer direct implementation over caller references when both exist.
