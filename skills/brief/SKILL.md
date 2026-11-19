---
name: brief
description: Turn messy requirements into a written brief with acceptance criteria before building. Use at the start of any non-trivial task, when the user pastes a Slack thread, ticket, spec or notes, asks to "start", "build", "implement" or "plan" something, or when requirements are unclear. Not for small one-file fixes.
---

# Brief

Goal: get from messy context to a short brief the user has approved, before any code is written. The user edits drafts; don't make them write from scratch.

1. Read what they pasted. Sort every item into **Stated** (with source), **Inferred** (say why), or **Missing**.
1b. **Framing check.** Separate what was observed from the stated cause, and the problem from the proposed solution. For each stated cause, say whether it has been verified in code (cite `file:line`) or is only claimed. If a cause is unverified, put it in Missing and don't plan around it. Skip for mechanical changes (a rename, a version bump).
2. For anything about the code, read the code and cite `file:line`. Until then it stays **Inferred**. Never fill gaps with plausible guesses.
3. Ask only about the **Missing** items, a few at a time, with a recommended answer for each.
4. Draft acceptance criteria as "given X, expect Y". Each must be checkable.
5. Add "How the agent checks its own work": tests that must exist, commands that must be clean, and a seed or manual check with the expected result.
6. List open questions that are the user's to decide.
7. Show the brief, using the structure in `brief_template.md` (in this skill's folder). Wait for approval.
7b. **Plan check.** Before building, review the plan for feasibility: does each step have a way to be checked? Which step is most likely to loop (queries, schemas)? Is anything in scope that the brief says is out of scope? Report problems before writing code.
7c. **Save it (every time the brief is approved, before writing any code).** First ask once: "New project, or a task in an existing one?" List the folders under `Projects/` and recommend one. Never pick the project yourself or create one without that answer. Then:
   - If new, follow the `new-project` skill (goal required). If existing, use the one they name.
   - Make the task with `python3 -I "$(cat ~/.config/obsidian-brain/script)" task "<project>" "<title>" "<goal>" "<next step>"`, then `... currentwork`. If the task already exists, don't overwrite it.
   - Save the approved brief as `BRIEF-YYYY-MM-DD.md` in the task folder (`Projects/<project>/Active-Work/<task>/`) and add one line linking it under `## Live Notes` in the task's STATUS.md. Do not put it in `handoff:`, that field is for HANDOFF files.
   - Report the paths in one line. Never touch other tasks. If there are more than 4 tasks in flight, warn once and still save.
8. Once approved and saved, build against the criteria and finish with "Decisions and assumptions" (verified/inferred, with sources).
