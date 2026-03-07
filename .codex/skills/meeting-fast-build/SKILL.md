---
name: meeting-fast-build
description: 在 interact-classroom 项目中执行会议本地打包流程。用户提到“会议快速构建”“本地打包会议”“更新 @cnstrong/webrtc 版本”“提交 dist”“推送远端”时使用。
---

# 会议快速构建

## Overview

在 `interact-classroom` 仓库中执行会议构建发布链路：检查并处理 `@cnstrong/webrtc` 版本更新、安装依赖、构建、仅提交 `dist/`、推送远端。

## Workflow

1. 检查仓库状态。
- 执行 `git status --short`。
- 识别无关脏改动并保留，不回滚。

2. 判断是否需要更新 `@cnstrong/webrtc`。
- 读取 `package.json` 中 `@cnstrong/webrtc` 当前版本。
- 若用户给出目标版本且与当前不一致，更新 `package.json`（推荐 `yarn add @cnstrong/webrtc@<version>`）。
- 若版本未变化，跳过版本更新步骤。

3. 安装依赖。
- 若第 2 步发生版本更新，执行 `yarn install`（或 `yarn`）并确保 `yarn.lock` 同步。
- 若未更新版本，可跳过安装，除非用户明确要求重装依赖。

4. 执行本地打包。
- 执行 `yarn build`。
- 若构建失败，输出首个关键报错并停止提交流程。

5. 核对构建产物。
- 执行 `git status --short`。
- 确认 `dist/` 已更新，必要时执行 `git diff -- dist` 抽查。

6. 仅提交 `dist`。
- 只暂存 `dist/`：`git add dist`。
- 提交信息固定：`build: dist`。
- 禁止将 `package.json`、`yarn.lock` 或其他文件加入本次提交，除非用户明确要求。

7. 推送远端。
- 执行 `git push` 推送当前分支。
- 输出 push 结果与最新 commit hash。

## Output Rules

- 明确报告是否更新了 `@cnstrong/webrtc` 版本。
- 明确报告构建、提交、推送三个阶段是否成功。
- 成功时输出 commit hash；失败时输出可定位的命令和关键报错。
