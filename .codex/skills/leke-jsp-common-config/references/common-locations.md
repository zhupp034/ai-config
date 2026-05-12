# Common Leke JSP Locations

Use this reference for concrete local paths and lookup patterns. Verify paths in the current workspace before editing because local checkouts can drift.

## Shared JSP Includes

- Shared header/footer/navigation repo:
  `/Users/zpp/Desktop/gitlab/leke-common-page`
- Legacy left navigation include:
  `/Users/zpp/Desktop/gitlab/leke-common-page/src/main/resources/META-INF/resources/pages/navigate/navigate.jsp`
- PC variant:
  `/Users/zpp/Desktop/gitlab/leke-common-page/src/main/resources/META-INF/resources/pages/navigate/navigate-pc.jsp`
- Common header examples:
  `/Users/zpp/Desktop/gitlab/leke-common-page/src/main/resources/META-INF/resources/pages/header/header.jsp`
  `/Users/zpp/Desktop/gitlab/leke-common-page/src/main/resources/META-INF/resources/pages/header/header-repo.jsp`

## Shared Scripts And Navigation

- Shared business scripts repo:
  `/Users/zpp/Desktop/gitlab/leke-scripts-business`
- Legacy navbar renderer:
  `/Users/zpp/Desktop/gitlab/leke-scripts-business/src/main/resources/META-INF/resources/scripts/navigate/navbar.js`
- PC navbar renderer:
  `/Users/zpp/Desktop/gitlab/leke-scripts-business/src/main/resources/META-INF/resources/scripts/navigate/navbar-pc.js`
- Role menu directory:
  `/Users/zpp/Desktop/gitlab/leke-scripts-business/src/main/resources/META-INF/resources/scripts/navigate/navs/`
- Role menu naming:
  `nav_${roleId}.js` for legacy left menu, `nav_pc_${roleId}.js` for PC personal-center style menu.

## Menu Text And i18n

- Chinese nav labels:
  `/Users/zpp/Desktop/gitlab/leke-scripts-business/src/main/resources/META-INF/resources/i18n/nav_zh_CN.properties`
- Default/English nav labels:
  `/Users/zpp/Desktop/gitlab/leke-scripts-business/src/main/resources/META-INF/resources/i18n/nav.properties`
- Literal Chinese labels can also appear directly in role nav files; only i18n keys like `nav.repo` need properties updates.

## Current Example: Question Researcher Home

- Business page repo:
  `/Users/zpp/Desktop/gitlab/leke-question`
- Page route:
  `/auth/researcher/researcherIndex.htm`
- Controller:
  `leke-question/src/main/java/cn/strong/leke/question/controller/IndexController.java`
- JSP:
  `leke-question/src/main/resources/META-INF/resources/pages/auth/researcher/researcherIndex.jsp`
- Shared left nav include:
  `leke-common-page/.../pages/navigate/navigate.jsp`
- Renderer:
  `leke-scripts-business/.../scripts/navigate/navbar.js`
- 教研员 role menu:
  `leke-scripts-business/.../scripts/navigate/navs/nav_402.js`

## Useful Search Commands

```bash
rg -n "visible text|route|seajs.use|include file|jNavbar" .
rg --files /Users/zpp/Desktop/gitlab | rg '/pages/navigate/navigate\\.jsp$'
rg --files /Users/zpp/Desktop/gitlab | rg 'scripts/navigate/navbar\\.js$'
rg -n "key: '菜单名'|url: .*route|spm: 402" /Users/zpp/Desktop/gitlab/leke-scripts-business/src/main/resources/META-INF/resources/scripts/navigate/navs
rg -n "nav\\.repo|nav\\.myleke|菜单名" /Users/zpp/Desktop/gitlab/leke-scripts-business/src/main/resources/META-INF/resources/i18n
```

## Edit Boundaries

- `leke-question`, `leke-paper`, `leke-beike`, `leke-voice`, and similar repos often own JSP pages and controllers.
- `leke-common-page` owns shared JSP wrappers.
- `leke-scripts-business` owns shared Seajs modules, navigation definitions, i18n labels, and many legacy static assets.
- `leke-tutor` often owns user context APIs such as `/auth/global/tutor/common/getMiniMenu.htm`; do not edit it for legacy left menu content unless tracing proves the menu is API-driven.
