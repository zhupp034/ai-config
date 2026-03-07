# Weekly Summary Template

Use this structure after collecting commit data with `scripts/collect_weekly_commits.py`.

## Recommended Output

```markdown
# 本周开发总结

统计周期：2026-03-02 至 2026-03-08

## 总体情况
- 活跃仓库数量
- 主要工作方向 2-4 条

## 各项目进展
### repo-a
- 功能 / 迭代
- 修复 / 优化
- 构建 / 依赖 / 发布

### repo-b
- 功能 / 迭代
- 修复 / 优化

## 风险与备注
- 提交信息过于简略的仓库
- 本周无提交但需要跟进的项目
```

## Compression Rules

- Merge repeated commit subjects into one theme.
- Prefer "completed X" over copying raw commit messages.
- Mention file paths only when they clarify the scope of the change.
- Keep the final summary shorter than the raw commit list.
