---
name: classroom-user-status-analyzer
description: Analyze compact user-info tuples and socket log payloads from the interact-classroom project by applying its formatUser, status-bit, permission-bit, role, client, and sort rules. Use when Codex is asked to view or format userInfo arrays, inspect teacherinfo/studentinfos/myself/change-list entries, explain a teacher or student's classroom/meeting state, or diagnose contradictions between online flags, permissions, invitations, and media URLs.
---

# Classroom User Status Analyzer

Analyze a target user from an interact-classroom socket log and report the exact
formatted state plus a concise diagnosis.

## Workflow

1. Identify the source of truth before decoding.
   - In an interact-classroom checkout, read `src/utils/businessUtil.ts` for
     `formatUser`, `formatUserStatus`, and `formatPermissionStatus`.
   - Read `src/services/businessConst.ts` for `PersonType`, `RoleIdMap`,
     `PersonTypeToRoleId`, `ClientType`, and `ClassVersionType`.
   - Treat current project code as authoritative if it differs from the bundled
     script.
2. Locate the target tuple in keys such as `teacherinfo`, `studentinfos`,
   `myself`, or user change lists. Do not confuse the log envelope's `userInfo`
   object with the compact tuple inside `message`.
3. Determine the mode.
   - Use meeting rules when `version === ClassVersionType.meeting`, the route is
     a meeting route, or the user explicitly says it is a meeting.
   - Otherwise use classroom rules. For an ambiguous record payload, state the
     assumption and retry with the other mode when it affects the result.
4. Run the bundled parser. Prefer a stable selector instead of dumping every
   student.

```bash
python3 ~/.codex/skills/classroom-user-status-analyzer/scripts/analyze_user_status.py \
  /path/to/log.txt --teacher

python3 ~/.codex/skills/classroom-user-status-analyzer/scripts/analyze_user_status.py \
  /path/to/log.txt --user-id 10402602

python3 ~/.codex/skills/classroom-user-status-analyzer/scripts/analyze_user_status.py \
  /path/to/log.txt --name 'student name' --meeting
```

5. Report these groups separately:
   - Identity: ID, name, role, person type, client type, group.
   - Presence and interaction: online, hand raised, talking, connecting, muted,
     person permission, audio/video invitations.
   - Granted capabilities: audio, video, drawing, and screen permissions.
   - Media data: normalized audio/video URLs and avatar.
   - Sorting: calculated `sort` value and mode.
   - Anomalies: for example, a media URL exists while its permission bit is
     false.

## Tuple Schema

Interpret the tuple indexes as follows:

```text
0 userId
1 status
2 videoUrl
3 audioUrl
4 legacy personType (formatUser does not read this value)
5 reserved
6 userName
7 online
8 clientType
9 permissionType
10 avatar
11 other (assistantGroupId and optional roleId)
```

Preserve the distinction between the fields:

- `status` drives interaction flags and the derived person type.
- `permissionType` drives `canAudio`, `canVideo`, `canDraw`, and `canScreen`.
- `online` is coerced independently to a boolean.
- A media URL only proves that an address was returned. It does not override
  permission or talking flags.
- Classroom and meeting modes decode person type and calculate `sort`
  differently.

## Output Rules

- Reply in the user's language.
- Show the target raw tuple and formatted object when useful.
- Translate booleans into direct human conclusions without hiding raw values.
- Name the evidence for any diagnosis. Avoid inferring "currently speaking"
  from `audioUrl` alone.
- If no unique user matches, list the candidate IDs/names briefly and ask for a
  selector instead of guessing.
