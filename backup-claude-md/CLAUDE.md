# Working agreements

## Claims about code
- Any statement about how the code behaves (function exists, query returns X, field is Y) must cite `file:line`. If you haven't read it in this session, mark it **inferred**, not fact.
- Never reuse a claim from earlier notes, summaries or prior sessions as fact without re-checking it against the code. Say "from notes, unverified" instead.
- If I ask "did you check that?", answer honestly: checked in code (where), or assumed.

## Non-trivial tasks
- Before building anything non-trivial (more than one file, any query or schema change, or anything from pasted requirements), ask whether a brief exists. If not, run the `brief` skill first. Don't start coding until I've confirmed the acceptance criteria.
- Don't decide open questions for me. List them and ask.

## End of task
- Finish with "Decisions and assumptions": each item says what was decided, what was rejected, and verified/inferred with a source.
- Tell me which checks you ran (tests, `node scripts/check.js --scope=local`) and their results. If something wasn't run, say so.

## Logging (Obsidian daily dev note)
- Only when I say "log this": use the `log` skill (one tagged line: finding, decision, pr, blocked). Don't log on your own. A Stop hook already logs task and commit changes with no tokens.

## Several tasks in flight (I get overwhelmed and lose the thread)
- One task is **active** per session, but several sessions (agents) can each have their own active task at once. Others are **parked**. A task in flight has `Active-Work/<task>/STATUS.md` (template: `~/.claude/templates/STATUS.md`). A SessionStart hook lists them. When a task is done, set `status: done` and move it with `python3 -I ~/Documents/ObsidianRecovered/Brain/scripts/brain.py finish <project> <task>`, which moves it to `Finished-Work/<task>/` and fixes links; never leave a done task in `Active-Work`.
- Start of a session: say "Current task: X. Parked: Y, Z." in one line.
- When I pick a task (by name or by its number in the hook's list): read its STATUS.md and the handoff's "Start here" block if there is one, and set its `status:` to `active`. Don't touch other `active` tasks (another session may own them); only park one if I say so. Then give me its next step. Don't read the full handoff unless I ask.
- If I ask for something new mid-task, ask once "switch now, or stay on the current task?" and write nothing until I answer. If I say park, write the STATUS.md stub then.
- Before parking or handing off, update STATUS.md (one next step) and write a handoff from `~/.claude/templates/HANDOFF.md`. Save it in the same task folder as STATUS.md as `HANDOFF-YYYY-MM-DD.md`, and put that filename in STATUS.md's `handoff:` line. Its "Start here" block is 5 lines or fewer.
- "Where was I?": answer in 3 lines or fewer (doing, last finished, one next step) and name the files used.
- More than 4 tasks in flight: say so and ask what to finish or drop. Warn, don't block.
- Reply short, one question at a time, and end with one concrete next step.
- Save tokens: keep replies under about 8 lines unless I ask for detail, no long tables after every step, and don't re-run checks that can't have changed. Update STATUS.md (`last_done`, `next`) only when I say "close out" or park the task, and don't ask "want this in last_done too?" after each step.
- Where things live: hook `~/.claude/hooks/task-status.sh` (SessionStart in `~/.claude/settings.json`), templates `~/.claude/templates/`, cheat sheet `~/Downloads/ObsidianVault/Projects/Claude-Projects/task-tracking-cheatsheet.md`.

## How to write to me (I have ADHD)
- Lead with the answer or result in the first 1-2 lines. Detail only after, and only what I need.
- Short sentences, bullets over paragraphs, bold the one thing I must not miss.
- Put anything comparable (options, before/after, timings, per-tile or per-file results) in a table, not prose.
- One topic and one question at a time. End with one concrete next step.
- Don't bury caveats. Put what is unverified or not run in its own short list.

## Session hygiene
- If a session passes roughly 150 of my messages, suggest a short handoff note and a fresh session.
