---
name: leke-jsp-common-config
description: Use when locating or changing shared configuration used by Leke JSP pages, including /pages includes, common headers, left navigation menus, role nav files, i18n labels, public JS/CSS assets, and cross-repo JSP resource ownership under local gitlab workspaces.
---

# Leke JSP Common Config

## Overview

Use this for old Leke JSP pages whose visible UI is assembled from shared JSP includes and shared static scripts rather than from the current business repo alone. Typical examples are left menus, headers, role switchers, footers, global toolbar entries, common tab bars, and menu labels.

## Core Workflow

1. Start from the current page.
- Search the current repo for the exact JSP route, include path, text, icon class, and script module:
  `rg -n "route|visible text|include file|seajs.use|jNavbar|Leke.user" .`
- Identify whether the visible element is local page content, a shared include, or a shared script-rendered component.

2. Follow shared JSP includes.
- For includes like `/pages/header/header.jsp`, `/pages/navigate/navigate.jsp`, or `/pages/foot/foot.jsp`, search all local GitLab repos if the file is absent in the current repo:
  `rg --files /Users/zpp/Desktop/gitlab | rg '/pages/(header|navigate|foot)/.*\\.jsp$'`
- Treat `leke-common-page` as the usual owner for shared JSP fragments.

3. Follow shared scripts.
- For `seajs.use('navigate/navbar.js')` or similar, search the local GitLab root for the module:
  `rg --files /Users/zpp/Desktop/gitlab | rg 'scripts/.*/navbar.*\\.js$'`
- Treat `leke-scripts-business` as the usual owner for shared business scripts, navigation definitions, i18n files, and common legacy assets.

4. Resolve role-specific menu files.
- Read the renderer first. For legacy left navigation, `navigate/navbar.js` loads `./navs/nav_${Leke.user.currentRoleId}`.
- Then open the matching role file, for example `scripts/navigate/navs/nav_402.js` for 教研员.
- Verify role IDs from local code or constants when uncertain; do not assume from memory if the change is role-sensitive.

5. Change the true source of configuration.
- Menu structure, order, icons, URLs, `spm`, `target`, and visibility predicates belong in role nav JS files.
- Text keys like `nav.myleke` and `nav.repo` belong in i18n files such as `i18n/nav_zh_CN.properties` and often `i18n/nav.properties`.
- JSP wrapper/layout conditions belong in `leke-common-page` shared JSPs.
- Business page behavior belongs in the owning business repo, not the shared config repo.

6. Verify across the include chain.
- Re-run targeted `rg` to confirm the updated token has one intended source.
- Check the changed repo's `git status` and avoid mixing unrelated local changes.
- If the user asked for a runnable verification, start the relevant app or use the deployed/local URL with browser verification. For pure config location answers, evidence from source paths and line references is enough.

## Known Local Map

Load [references/common-locations.md](references/common-locations.md) when working on a real Leke JSP public config change or when you need examples of common files.

## Integration With Search Skill

If ownership is unclear, first use `gitlab-leke-code-search` to locate the page or implementation. After ownership is known and the task is about common JSP/menu/header/static configuration, use this skill to trace and edit the shared config layer.

## Reporting

Default to Chinese. Always state:

- `当前页面来源`: business repo and route/controller/JSP evidence.
- `公共配置来源`: shared JSP/script/i18n file evidence.
- `应修改位置`: exact file and whether it is menu config, i18n text, wrapper JSP, icon/style, or business logic.
- `影响范围`: roles/pages likely affected because shared files are cross-repo assets.
- `验证方式`: source search, build/test command, or browser check used.

## Common Mistakes

- Do not edit only the current business JSP when the element is rendered by `/pages/navigate/navigate.jsp` or another shared include.
- Do not treat `getMiniMenu.htm` as the left JSP menu source without evidence. It commonly supplies user context for modern headers, while legacy left menus may be static role JS files.
- Do not change only `nav_zh_CN.properties` when the key also needs an English fallback in `nav.properties`.
- Do not hardcode production domains when the existing nav file uses `Leke.domain.*ServerName`.
- Do not commit changes in `leke-question` when the real menu source is `leke-scripts-business` or `leke-common-page`.
