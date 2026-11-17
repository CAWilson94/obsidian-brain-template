# 📓 Obsidian Brain Template

A work-brain vault for Obsidian: a Home page with a banner, live tables of tasks, epics, daily notes and 1-2-1s, and templates with emoji callouts that explain each section. Modelled on a Notion "wiki" workflow.

## 5-minute setup
1. Copy this repo (or "Use this template" on GitHub), then **Open folder as vault** in Obsidian (1.15 or newer; Bases is built in).
2. Settings, Community plugins, turn off Restricted mode, install and enable **Templater**.
3. Templater settings: set **Template folder location** to `Templates`.
4. Settings, Appearance, CSS snippets: enable `banner`.
5. Open `Home`. Delete the `Examples` folder when you are ready.

## Daily use
- New task / daily note / 1-2-1 / epic / side quest: command palette, "Templater: Create new note from template". Each gets a random emoji in its title that no other note title starts with. Change it by hand any time.
- Put notes in `Tasks`, `Daily`, `Meetings`, `Epics`. Tables find notes by the `type` property, not the folder.
- Link tasks from the daily note with `[[wikilinks]]`; each task lists the daily notes that mention it.
- Filter by tags: add `tags: [ui, bug]` to a task, then add a filter in the Base.

## Properties (frontmatter)
| Note | Properties |
|---|---|
| Task | type, status, tags, created, ticket, branch, pr, summary |
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
