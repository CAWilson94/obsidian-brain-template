---
name: close-out
description: End-of-session update for the task you worked on. Use when the user says "/close-out", "close out", "wrap up" or "park this". Writes one new last_done and one next step to the task's STATUS.md (and PR or issue numbers that came up), in a single confirmed edit. Never edits other tasks.
---

# Close out

Goal: update the task card once, at the end, instead of after every step. Keep it short: one proposal, one confirmation.

## Steps
1. **Which task?** The one this session worked on. If it is unclear, ask once. Never touch another task (another session may own it).
2. **Read** its `STATUS.md` (`title`, `status`, `last_done`, `next`, `pr`, `issue`) from `Projects/<project>/Active-Work/<task>/`.
3. **Propose in one block** (from what happened in this session, not from memory or guesses):
   - `last_done`: ONE short line, facts only, overwritten each time. Put anything longer in the task's body under `## Live Notes` as a `### YYYY-MM-DD` heading (newest at the bottom). Never add `last_done_2` and the like.
   - `next`: ONE concrete step. If you cannot tell what it should be, ask for it. Do not invent it.
   - New PRs or issues that came up: add PRs you raised to `pr:` as full URLs (a bare number also works), and issues to `issue:`.
   - Status change if it applies: `parked`, or `done`.
4. Ask once: "Write this?" On yes, edit only those header lines (single-quote values that contain `: `, double inner `'`), then:
   - If the status is now `done`: run `python3 -I "$(cat ~/.config/obsidian-brain/script)" finish "<project>" "<task folder>"`.
   - Otherwise run `... currentwork` so Home shows it.
5. Do NOT log to the daily note unless the user says "log this". The Stop hook already adds `[auto]` lines for the `last_done` and `next` change.
6. Reply in 3 lines or fewer: what changed, anything not checked, one next step.

## Never
- Never write without the user's yes.
- Never claim something is finished or verified that this session did not check.
- Never touch more than one task per run.
