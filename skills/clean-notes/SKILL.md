---
name: clean-notes
description: Walk the user through the "Needs attention" list in their Obsidian vault, one item at a time. Use when the user says "/clean-notes", "clean my notes" or "go through needs attention". First tasks whose PR has merged but whose status is still active (close, keep or update), then projects with an empty goal (suggest one, the user edits). Writes only after the user answers.
---

# Clean notes

Goal: clear the 🧭 Needs attention card on `Home.md` together, one item at a time.
Vault: `Home.md` and `scripts/` sit together in BRAIN, the parent of the folder the path in `~/.config/obsidian-brain/script` points into. `Projects/` sits in BRAIN, or in its parent when the vault keeps the brain in a subfolder (read `VAULT` at the top of `brain.py`). Reply short, one question at a time, bold what matters, end with one next step.

## 0. Refresh and count
```
python3 -I "$(cat ~/.config/obsidian-brain/script)" check
```
Then say: "N things: A merged-PR tasks, B empty goals, C other." Read the list from `Home.md` between `chk:start` and `chk:end`. Start with merged-PR tasks.

## 1. Merged PR, task still active (one task per turn)
For each task, read its `STATUS.md` (`title`, `pr`, `last_done`, `next`, `blocked`). Show in a 4-line block:
- Task and the merged PR (number, merge date from `gh pr view <n> -R <gh_repo from .brain.json at the vault root> --json state,mergedAt,title`)
- Its current `next`
- Whether `next` or `blocked` still make sense now that the PR merged (say plainly if it looks stale; cite the field)

Ask ONE question with these options:
| Choice | What you write |
|---|---|
| **Done** | `status: done`; `last_done:` = today + "PR #n merged <date>"; `next: none`; `blocked: nothing`; then move it: `python3 -I "$(cat ~/.config/obsidian-brain/script)" finish "<project>" "<task folder>"` (moves it to `Finished-Work/` and fixes links) |
| **Keep, new next step** | the user gives the next step; update `next`, drop stale `blocked`, add the merge to `last_done` |
| **Park** | `status: parked`; ask the user for the one next step |
| **Skip** | write nothing |

Rules:
- Never close a task, or invent a next step, without their answer. A follow-up step is their decision.
- When a task has several `pr:` numbers, check them all before asking.
- Edit only the header lines. Single-quote values that contain `: ` and double inner `'`. Keep the other fields as they are.

## 2. Empty project goal (one project per turn)
For each project, read `Projects/<name>/<name>.md`, the `goal:` of its tasks in `Active-Work/*/STATUS.md`, and any `_START-HERE.md` or README there. Propose ONE goal line (what changes, for whom, under 20 words) and say which files it came from. Options: **use it**, **the user edits it** (the user types their own), **skip**. Write `goal:` in the project file's front matter only on their answer.

## 3. Other findings
Empty `title`, `status`, `goal`, `next` on a task, or a `pr:` that is not a PR number: show the one line, ask what the value should be. Do not guess values.
A task that is `done` but still in `Active-Work`: ask, then run the `finish` command above. A task in `Finished-Work` that is not `done`: ask whether to set it to `done` or move it back to `Active-Work`.

## 4. Finish
Run `brain.py check` again. Report in a table: closed, parked, goals set, skipped, still open. Say which checks ran. End with one next step. Do NOT log to the daily note unless the user says "log this".

## Never
- Never edit more than one task per answer.
- Never touch `Home.md` by hand; `brain.py` rewrites the card.
- Never claim a task is finished from a PR alone. A merged PR is a prompt to ask the user, not proof.

## Needs `.brain.json`
The GitHub check only runs when `.brain.json` at the vault root has `"gh_repo": "owner/name"`. If it is empty, say so once and skip the merged-PR step.
