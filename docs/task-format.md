# Task and project format

## Folders
```
Projects/
  <Project>/
    <Project>.md                 the project page
    Active-Work/
      <task-folder>/             one task = one folder
        STATUS.md                the task's card
        BRIEF-<date>.md          anything else, as needed
        HANDOFF-<date>.md        handoff for a fresh session
    Finished-Work/
      <task-folder>/             a done task
    GitHub/
      <repo>-pr-<n>.md           one note per PR or issue
```
Every card is called `STATUS.md` on purpose: the folder name is the task's name, and the hook, Home and `brain.py` all look for that file.

## STATUS.md fields
Put them in the `---` block at the top. Copy `Templates/STATUS.md` to start.

| Field | Holds |
|---|---|
| `title` | Short name, with an emoji |
| `tags` | The project tag, so Home colours the chip |
| `pr` | PRs you raise, as full URLs: `['https://github.com/owner/repo/pull/1']`. A bare number works when `gh_repo` is set |
| `issue` | Issue URLs this task is about |
| `links` | Other related PRs, issues, threads (full URLs) |
| `status` | `active`, `parked` or `done` |
| `goal` | One line: what changes, for whom |
| `last_done` | **One short line**, overwritten each time |
| `next` | ONE concrete next step |
| `blocked` | What's stopping it, or `nothing` |
| `handoff` | The handoff file name, or `none` |

Rules:
- Wrap a value in single quotes if it contains `: `. Put URLs in a `[ ]` list inside quotes.
- No `# comment` after a value: the tools read the whole line.
- History goes in the body under `## Live Notes`, one `### YYYY-MM-DD` heading per day, newest at the bottom.

## Finishing a task
Set `status: done`, then `python3 scripts/brain.py finish "<Project>" "<task-folder>"`. It moves the folder to `Finished-Work/` and fixes links to it. `brain.py check` flags a done task left in `Active-Work/`.

## Handoffs
Start from `Templates/HANDOFF.md`. Save it in the task's folder as `HANDOFF-YYYY-MM-DD.md` and put the file name in `handoff:`. Keep its "Start here" block to 5 lines.

## GitHub notes
`python3 scripts/brain.py githubnotes` makes one note per PR or issue under `Projects/<project>/GitHub/`, built from every task's `pr`, `issue` and `links`. Each note lists the tasks that use it, and the project page shows them in a table. It needs the `gh` CLI. `brain.py auto` runs it in the background at most every 20 minutes. Add `"epics": ["owner/repo#123"]` to `.brain.json` to mark issues as epics.

## Properties for other notes
| Note | Properties |
|---|---|
| Project page | type, status, tags, goal |
| Daily | type, date, tags (`<month>-<year>-dev`, e.g. `november-2026-dev`) |
| 1-2-1 | type, person, date, tags |
| Epic | type, status, tags, created, issue, link |
| Side quest | type, status (Idea, Exploring, Done, Dropped), tags, created, why, next |

## Daily to-dos
The **🎯 Today** card on Home reads the `## Daily TODO` section of today's daily note ("3 of 5 done"). Unticked items from the last daily note are copied into today's note once, the first time Home refreshes that day. Tick boxes in the daily note.
