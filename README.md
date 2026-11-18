# 📓 Obsidian Brain Template

A work-brain vault for Obsidian: a Home page with a banner, live tables of tasks, epics, daily notes and 1-2-1s, and templates with emoji callouts that explain each section. Modelled on a Notion "wiki" workflow.

## 5-minute setup
1. Copy this repo (or "Use this template" on GitHub), then **Open folder as vault** in Obsidian (1.15 or newer; Bases is built in).
2. Settings, Community plugins, turn off Restricted mode, install and enable **Templater**.
3. Templater settings: set **Template folder location** to `Templates`.
4. Settings, Appearance, CSS snippets: click reload, then enable `banner`, `home-grid`, `notion-look` and `tag-colours`. Open `Home` in Reading view (Cmd+E) to see the two-column grid.
5. Open `Home`. Delete the `Examples` folder when you are ready.

## Daily use
- New daily note / 1-2-1 / epic / side quest: command palette, "Templater: Create new note from template". Each gets a random emoji in its title that no other note title starts with. Change it by hand any time.
- Put notes in `Daily`, `Meetings`, `Epics`, `SideQuests`. Tables find notes by the `type` property, not the folder.
- **Today card on Home:** shows today's `## Daily TODO` ticks ("3 of 5 done"), the list, and tasks you closed this week. Unticked to-dos from the last daily note are copied into today's note once, the first time Home refreshes that day. Tick boxes in the daily note; Home follows within seconds if the watcher is on.
- Link tasks from the daily note with `[[wikilinks]]`; each task lists the daily notes that mention it.
- Filter by tags: add `tags: [ui, bug]` to a task, then add a filter in the Base.


## Scripts (for AI and the terminal, no Obsidian needed)
`scripts/brain.py` builds notes from the same Templater templates, so the headings never drift:
- `python3 scripts/brain.py new daily` (also `side-quest "title"`, `epic "title"`, `1-2-1 Person`, `project Name`)
- `python3 scripts/brain.py log "[finding] text"` appends a timestamped bullet to today's Daily Dev Note (tags: finding, decision, pr, blocked)
- `python3 scripts/brain.py auto` logs changes to a task's `last_done`/`next` and new git commits. Run it from a hook to log with zero model tokens.
- `python3 scripts/brain.py stats` and `dashboard` rewrite `Stats.md` and `Dashboard.html` (a coloured, Notion-style page that opens in a browser). The hook runs both after `auto`.
Nothing is ever overwritten.

## Skills for Claude Code
`./install.sh` links the skills in `skills/` into `~/.claude/skills/` and tells them where this brain lives (`~/.config/obsidian-brain/`). Start a new Claude Code session afterwards.
| Skill | What it does |
|---|---|
| `log` | "log this": adds one tagged line to today's Daily Dev Note |
| `new-project` | Starts a project (always asks for a goal) and adds a task to it when you ask |
| `close-out` | Updates the task you worked on once at the end of a session: `last_done`, `next`, PRs (one confirmed edit) |
| `clean-notes` | Walks the Home "Needs attention" list one item at a time: tasks whose PR merged, empty project goals |
| `cha-generic-review` | Reviews a GitHub PR against `rules/review-rules.md`. Edit those rules to your own |

Set `"gh_repo": "owner/name"` in `.brain.json` so PR numbers become links and `python3 scripts/brain.py check` can see which PRs have merged. Leave it empty to skip that.
STATUS.md also takes `pr: [123]` (PRs you raised), `issue: [url]` and `links: [url]`.

## The whole workflow (one loop)
| Step | What you do | What runs |
|---|---|---|
| 1. Start | Open a Claude Code session in your repo | SessionStart hook `hooks/task-status.sh` lists your in-flight tasks (needs `jq`) |
| 2. Work | Change a task's `STATUS.md` when something moves: `last_done`, `next`, `pr`, `issue`, `links` | Stop hook runs `brain.py auto`: logs the change to today's daily note as `[auto]` and refreshes Home |
| 3. Capture | Say **"log this"** for a finding or decision | `log` skill adds one tagged line to the daily note |
| 4. Tidy | When Home's **Needs attention** card is not empty, run `/clean-notes` | `brain.py check` refreshes it (the GitHub part needs `gh_repo` in `.brain.json` and the `gh` CLI logged in); the skill then goes through it one item at a time |
| 5. Review | `/cha-generic-review <PR url>` | Reads `rules/review-rules.md` and the PR; posts nothing |
| 5b. Close out | `/close-out` at the end of a session | Updates the task card once (`last_done`, `next`) |
| 6. Save | Commit the vault | Plain git |

### Set up the hooks
Run `./install.sh` first (the SessionStart hook reads the path it saves). Then add this to `~/.claude/settings.json` (merge it into any existing `hooks` block), with your own paths. `SessionStart` lists your tasks at the start of a session (step 1). `Stop` makes step 2 happen by itself.
```json
{
  "hooks": {
    "SessionStart": [
      { "hooks": [ { "type": "command", "command": "/path/to/this-vault/hooks/task-status.sh" } ] }
    ],
    "Stop": [
      { "hooks": [ { "type": "command", "command": "python3 -I /path/to/this-vault/scripts/brain.py auto >/dev/null 2>&1 || true" } ] }
    ]
  }
}
```
`auto` also rewrites the Current Work list and the Needs attention card in `Home.md`. It never calls GitHub, so it stays fast. Run `brain.py check` by hand for that.

### Keep Home fresh while you edit (optional, macOS)
Home's lists are rewritten by `brain.py`. The Stop hook does it when a Claude session ends; this watcher does it as soon as you save a **project note** (`Projects/<name>/<name>.md`, for example after changing its goal). It is push based, so it uses no polling and no model calls.
```bash
brew install fswatch
scripts/install_watch.sh          # needs install.sh run first; turn off with: scripts/install_watch.sh --off
```
It installs a login launch agent that runs a copy of `scripts/watch_projects.sh` from `~/.local/share/obsidian-brain/` (macOS will not let launchd run scripts that sit in `~/Documents`). Logs: `~/Library/Logs/obsidian-brain-watch.log`. Only project notes are watched, not task notes. Re-run `install_watch.sh` after you update `watch_projects.sh`.

### Good to know
- **Tag colours work in the Home lists but not inside Bases tables, lists or cards.** Obsidian draws a Bases tag without its name in the page, so CSS cannot colour tags per name there. That is why Home's Current Work list is generated as text with real `#tags`. Use Reading view (Cmd+E).
- `install.sh` replaces an existing *link* with the same skill name, but skips a real folder.
- Not tested yet: the three skills in a fresh Claude session.

## Folder structure
```
Projects/
  <Project>/
    <Project>.md                 the project: goal, tags, a live table of its tasks
    Active-Work/
      <task-folder>/             one task = one folder
        STATUS.md                the task's card (the fields the hook, Home and brain.py read)
        BRIEF-<date>.md          anything else for that task, as needed
        HANDOFF-<date>.md        handoff for a fresh session, in the same folder
    Finished-Work/
      <task-folder>/             a done task, moved here with `brain.py finish`
```
- **`STATUS.md` is the only file the tools read.** Everything else in the task folder is for you.
- **One `STATUS.md` per task folder.** The folder name is the task's name, so every card is called `STATUS.md` on purpose.
- **A handoff lives in its task folder** as `HANDOFF-YYYY-MM-DD.md`, and the task's `handoff:` field names the file (use `none` if there isn't one). Start one from `Templates/HANDOFF.md`.
- **A done task moves to `Finished-Work/`.** Set `status: done`, then run `python3 scripts/brain.py finish <project> <task-folder>`: it moves the whole folder and fixes any links to it. `Active-Work/` then only holds live tasks, and `brain.py check` flags a done task left behind.
- **Make them with `/new-project`** (a project, then a task when you ask), or copy `Templates/STATUS.md` into a new task folder by hand.

## Tasks
A task is a `STATUS.md` file in `Projects/<project>/Active-Work/<task>/`. Start from `Templates/STATUS.md` (copy it into a new task folder). `Templates/HANDOFF.md` is the matching handoff note for a fresh session. Keep the properties in the `---` block, and wrap a value in 'single quotes' if it contains ": ". The Current Work table reads them; `Projects/Example-Project` shows the shape.

## Properties (frontmatter)
| Note | Properties |
|---|---|
| Task (`STATUS.md`) | title, pr, issue, links, status (active, parked, done), goal, last_done, next, blocked, handoff |
| Daily | type, date, tags |
| 1-2-1 | type, person, date, tags |
| Epic | type, status, tags, created, issue, link |
| Side quest | type, status (Idea, Exploring, Done, Dropped), tags, created, why, next |

## Not verified yet (not tested inside Obsidian)
- The `sort:` lines in the `.base` files (check: edit the sort in the Base UI and compare the saved file).
- `Daily For Task.base` uses `file.hasLink(this.file)`. If it shows nothing, use the built-in Backlinks panel.
- The Templater random emoji and rename steps.

## Phase 2 (not built)
- Fireflies: pull meeting transcripts into 1-2-1 notes.

## Banner
`assets/banner.png` is a NASA-style astronaut photo. Check its licence before publishing, or swap in your own image with the same name.

## Privacy
This repo holds only fictional examples. Keep real notes in a separate private repo.
