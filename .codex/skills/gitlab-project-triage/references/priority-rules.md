# Priority Rules

Use these heuristics when classifying repositories.

## Language
- Triage reports default to Chinese.
- Repository names, paths, commands, and skill ids stay in English.

## P0
- Currently maintained or frequently changed
- User is likely to contribute next month
- Missing AI governance docs would create immediate audit risk

## P1
- Maintained but not central to near-term delivery
- Some docs exist, but governance work can wait until after P0

## P2
- Legacy, experimental, archived, or currently inactive
- Governance investment has low short-term return

## Recommended action mapping
- Missing baseline docs: use `$project-ai-init`
- Docs exist but trust is low: use `$project-ai-audit`
- Clearly inactive: record as P2 and stop
