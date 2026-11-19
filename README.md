# 📓 Obsidian Brain Template

A work brain for [Obsidian](https://obsidian.md) with a Notion-style Home page. It keeps your tasks, projects, daily notes and PRs in one place, and works with Claude Code skills so you spend little time on admin.

## 🚀 Quick start
1. **Use this template** on GitHub, then open the folder as a vault in Obsidian (1.15 or newer).
2. Settings, Community plugins, turn off Restricted mode, install and enable **Templater**. Its settings are already in the repo.
3. Settings, Appearance, CSS snippets: reload, then switch on `banner`, `home-grid`, `notion-look` and `tag-colours`.
4. Open `Home` and press **Cmd+E** (Reading view) to see the two columns.
5. Optional, for Claude Code: run `./install.sh` and start a new session. It links the skills below.
6. Delete `Examples/` and `Projects/Example-Project/` when you're ready.

## 🔁 How you use it
| When | You do | What happens |
|---|---|---|
| Start a project | `/new-project` | Asks for a goal, makes the project page |
| Work on a task | Edit its `STATUS.md` | Home updates (Stop hook, or the optional watcher) |
| Have a thought | say "log this" | One line goes into today's daily note |
| End of a session | `/close-out` | Updates the task's `last_done` and `next` once |
| Home looks messy | `/clean-notes` | Walks through what's in the **🧊 Stuck n' Stale** card |
| Review a PR | `/cha-generic-review <url>` | Checks it against `rules/review-rules.md`. Posts nothing |

## 🗂️ Folders
```
Projects/<Project>/
  <Project>.md            the project page: goal, GitHub items, tasks
  Active-Work/<task>/     one folder per task: STATUS.md, plus briefs and handoffs
  Finished-Work/<task>/   done tasks (moved with brain.py finish)
  GitHub/                 one note per PR or issue (made by brain.py githubnotes)
Daily/  Meetings/  Epics/  SideQuests/    notes made from the templates
Templates/  Bases/  scripts/  skills/  hooks/  rules/
```
`STATUS.md` is the only file the tools read. Details: [docs/task-format.md](docs/task-format.md).

## 🛠️ Commands
Run with `python3 scripts/brain.py <command>`. Nothing is ever overwritten. Most are called for you, so you rarely type them.

| Command | Does | Called by |
|---|---|---|
| `project "Name" "goal" [emoji]` | New project page | `/new-project` |
| `task "Project" "Title" "goal" ["next"]` | New task from the STATUS template | `/new-project` |
| `finish "Project" "task-folder"` | Move a done task to `Finished-Work/`, fix links | `/clean-notes`, `/close-out` |
| `log "[finding] text"` | Add a line to today's daily note | the `log` skill. Run it yourself for free (no model) |
| `currentwork` | Refresh the lists on Home | `/new-project`, `/close-out`, the file watcher |
| `check` | Find fields to fix and merged PRs (needs `gh`) | `/clean-notes`. Run it yourself to refresh GitHub data |
| `githubnotes` | Make and update the GitHub notes (needs `gh`) | `auto`, in the background. Run it yourself to force a refresh |
| `auto` | Log `[auto]` lines, refresh Home | the Stop hook |
| `new daily` / `side-quest` / `epic` / `1-2-1` | New note from a template | **you** (or Templater in Obsidian) |
| `stats`, `dashboard`, `css` | Stats page, dashboard page, tag colours | `auto` |

## 🔌 Optional extras
- **Hooks** (task list at session start, auto-log, auto-refresh) and the **file watcher**: [docs/hooks-and-watcher.md](docs/hooks-and-watcher.md).
- **GitHub links:** set `"gh_repo": "owner/name"` in `.brain.json` so PR numbers work.

## ⚠️ Good to know
- Tags are coloured in Home's lists, but not inside Bases tables (Obsidian doesn't expose the tag name there).
- Not tested inside Obsidian yet: the `sort:` lines in the `.base` files, and Templater's random emoji and rename steps.
- `assets/banner.png` is a NASA-style photo. Check its licence before publishing, or swap in your own.
- This repo holds fictional examples only. Keep real notes in a separate private repo.
