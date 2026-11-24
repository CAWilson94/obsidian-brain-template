---
name: handoff
description: Write a handoff note so a fresh session or another agent can pick a task up cold. Use when the user says "/handoff", "write a handoff", "hand this off" or "park this with a handoff". Writes HANDOFF-YYYY-MM-DD.md in the task folder from Templates/HANDOFF.md and points STATUS.md at it, in one confirmed edit. Never edits other tasks.
---

# Handoff

Goal: leave a note a cold session can act on in under a minute. Short "Start here", detail below only as reference.

## Steps
1. **Which task?** The one this session worked on. If unclear, ask once. Never touch another task (another session may own it).
2. **Read** its `STATUS.md` from `Projects/<project>/Active-Work/<task>/`, and the template `Templates/HANDOFF.md` (or `~/.claude/templates/HANDOFF.md` if the vault copy is missing).
3. **Draft from this session only**, not from memory or old notes:
   - **Start here (5 lines max):** goal and the ONE next step; state right now (what is running, broken or uncommitted, and when you checked); don't-touch list (branches, PRs, files); open questions the next agent must NOT decide.
   - **Detail:** context, decisions (only ones the user stated), a files table, gotchas, known risks.
   - Label every claim **verified** (read it, with `file:line`), **inferred**, or **stated** (the user said it). If you did not read it this session, mark it inferred or "from notes, unverified".
4. Show the "Start here" block and the proposed `next` line. Ask once: "Write this?"
5. On yes, in one go:
   - Save the note as `HANDOFF-YYYY-MM-DD.md` in the same folder as `STATUS.md`. If one exists for today, ask before overwriting.
   - Set `handoff:` in `STATUS.md` to that filename, and set `next:` to the ONE step. If the user said "park", set `status: parked`.
   - Run `python3 -I "$(cat ~/.config/obsidian-brain/script)" currentwork` so Home shows it.
6. Do NOT log to the daily note unless the user says "log this".
7. Reply in 3 lines or fewer: the file path, anything not checked, one next step.

## Never
- Never write without the user's yes.
- Never put more than 5 lines in "Start here".
- Never decide an open question for the user; list it.
- Never touch more than one task per run.
