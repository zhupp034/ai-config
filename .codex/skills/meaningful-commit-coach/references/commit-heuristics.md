# Commit Heuristics

Use these heuristics when reviewing a change set.

## Language
- Explanations and review advice default to Chinese.
- Commit messages, commands, paths, and code ids stay in English.

## Good commit properties
- One main intent
- Easy to explain in a code review
- Maps to a task, bug, test, or docs purpose
- Avoids unrelated generated output

## Common low-signal patterns
- Formatting mixed with behavior changes
- Tests bundled with unrelated refactors
- Dependency upgrades mixed with bug fixes
- Dist files committed together with source changes unless required by repo policy

## Review output
- Summarize current change groups.
- Identify noisy files.
- Suggest 1 to N commit groups.
- Provide Conventional Commit messages for each group.
