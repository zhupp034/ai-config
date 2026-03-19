# Structured Report Schema

当前 `git-weekly-summary` 输出的 JSON 作为周报链路的正式中间层，默认写入：

- `/Users/zpp/Desktop/workspace/git-weekly-report/YYYY-MM-DD.json`

## 顶层字段

- `report_type`: 固定为 `git-weekly-summary`
- `schema_version`: 当前版本 `1.0`
- `analysis_mode`: `rule` 或 `ai`
- `root`: 主扫描目录
- `roots`: 实际扫描目录列表
- `since`: 统计开始时间
- `until`: 统计结束时间
- `author`
- `author_email`
- `generated_at`
- `repositories`

## repositories[]

- `name`
- `path`
- `commit_count`
- `authors`
- `touched_files_count`
- `commits`
- `themes`

## commits[]

- `sha`
- `short_sha`
- `author`
- `author_email`
- `date`
- `subject`
- `body`
- `files`
- `diff`
- `analysis`

## commits[].analysis

- `summary`: 提交级摘要
- `files[]`: 关键文件分析
- `risks[]`: 提交级风险

## themes[]

- `title`: 主题标题
- `categories[]`: 主题涉及的提交类型
- `commit_count`
- `commit_shas[]`
- `key_files[]`
- `summaries[]`
- `analysis`

## themes[].analysis

- `completed_sections`
  - `需求开发[]`
  - `问题修复[]`
  - `技术优化[]`
- `project_summary[]`
- `risks[]`
- `reflections[]`
- `next_steps[]`

## 设计约束

- `themes.analysis` 是给 `weekly-report-summary` 消费的主数据源。
- 当 `analysis_mode=ai` 时，先生成 `commit.analysis`，再回填聚合出 `themes.analysis`。
- 当 `analysis_mode=rule` 时，依然会生成完整 `themes.analysis`，只是内容来自规则聚合，不依赖外部模型。
