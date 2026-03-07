# Git Commit Rules

- Git 提交信息必须使用 Conventional Commits。
- 允许的 type: feat, fix, docs, refactor, test, chore, build, ci.
- 提交信息格式：`type(scope): summary`；如果没有明确 scope，可使用 `type: summary`。
- `summary` 使用英文，动词短语，小写开头，尽量不超过 72 个字符。
- 未经用户明确要求，不主动执行 `git commit`。
- 如需提交，先检查变更范围，避免把无关文件一并提交。
