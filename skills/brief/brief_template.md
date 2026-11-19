# Brief template

Use before any non-trivial task. The agent fills it from the context you paste and asks you only about the gaps. You edit the draft instead of writing it cold.

## How to run it
1. Paste the messy context (Slack thread, ticket, spec, notes).
2. Ask the agent to sort it into **Stated**, **Inferred** and **Missing**. Every item gets a source.
3. You answer only the **Missing** items.
4. The agent drafts the acceptance criteria. You edit them.
5. Only then does the agent start building.

## Template

### Goal
One or two sentences: what changes for whom.

### Out of scope
What this task will not touch.

### Context
| Item | Status (stated / inferred / missing) | Source |
| ---- | ------------------------------------ | ------ |
|      |                                      |        |

Rule: anything about the code is **inferred** until the agent cites `file:line`.

### Facts to check in the code before building
- [ ] (claim) - checked at `path/to/file.ts:123`, or still inferred

### Acceptance criteria
Written as "given X, expect Y". Each one must be checkable.
1. Given ..., expect ...
2. Given ..., expect ...

### How the agent checks its own work
- Tests that must exist and pass:
- Commands that must be clean (your project's tests, type check and lint):
- Seed data or manual check, with the expected result:

### Open questions
Things you still need to decide. The agent must not decide these.

### At the end: decisions and assumptions
The agent fills this in when done. Each item: decision, alternatives rejected, **verified** or **inferred**, source.
