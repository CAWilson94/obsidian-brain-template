---
name: log
description: Append one tagged line to today's Daily Dev Note in the user's Obsidian brain vault. Use ONLY when the user says "log this", "log:", "add to my dev note" or "note this down". Never log on your own; a hook already logs task and commit changes for free.
---

# Log

Goal: capture one useful line in today's Daily Dev Note for almost no tokens.

## How
Run one command. Do not read the note first. Do not re-read it after.

```
python3 -I "$(cat ~/.config/obsidian-brain/script)" log "[tag] one line"
```

The script creates today's Daily Dev Note from the template if it does not exist, and appends `- HH:MM [tag] text`. It never edits or deletes older lines.

## Tags (pick the closest one)
| Tag | Use for |
|---|---|
| `[finding]` | something learned or measured |
| `[decision]` | something chosen, with the reason in the same line |
| `[pr]` | a PR or CI change (number, state) |
| `[blocked]` | something stopping their, and what is needed |

If the user did not say a tag, choose one. If nothing fits, use no tag.

## Rules
- One line per log, plain words, under about 200 characters. Put the file or PR number in the line when there is one.
- Log what the user told you or what you verified. Never log a guess as fact; write "(inferred)" if it is not checked.
- Ownership: only log work that is hers. A teammate's work gets "team context:" at the start of the line.
- Do not paste raw Slack or PR text. Write the point.
- If it reads like a confirmed decision, ask once at the end: "Want this in the task's STATUS.md `last_done` too?" Do not ask twice.
- Reply with one short line: what you logged. No summary.

## What happens without you
A Stop hook runs `brain.py auto`, which adds `[auto]` lines when a task's `last_done` or `next` changes in STATUS.md, or a new git commit appears. That costs no model tokens. Do not repeat those lines.
