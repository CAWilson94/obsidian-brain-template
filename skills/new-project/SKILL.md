---
name: new-project
description: Start a new project in the brain vault (a Projects/<name>/ folder with a goal and a tasks table), and add a task to a project when asked. Use when the user says "new project", "open a new project", "/new-project", "add a task to <project>" or "new task". Always asks for the goal first. Never makes a task unless the user asks for one.
argument-hint: <project name>
---

# New project

Goal: every project starts the same way, with a goal written down, so it never shows up as "goal is empty" later.
Reply short, one question at a time, end with one next step. Do not make files until you have the answers.

Run everything with the script the install saved:
`python3 -I "$(cat ~/.config/obsidian-brain/script)" <command>`

## New project
1. **Name.** If the user did not give one, ask for it. Use it as the folder name exactly as typed.
2. **Goal.** Ask: "What changes, and for whom? One line." This is required. If the user is unsure, offer one draft goal from what they told you and let them edit it. Do not make the project with an empty goal.
3. **Emoji.** Pick ONE emoji for the title yourself, related to the project. It can be literal or an obscure joke (a sink emoji for a project about syncing). Tell the user which one you picked and why in a few words, so they can change it. Do not ask them to choose.
4. Run: `... project "<name>" "<goal>" "<emoji>"`
   It makes `Projects/<name>/<emoji> <name>.md` (type project, tag from the name, the goal, a tasks table) and an empty `Active-Work/` folder, adds the project to Home with a coloured `#tag`, and regenerates the tag colours. It refuses to touch a project that already exists. With no emoji it picks a random unused one.
5. Report the path in one line. Then ask once: "Want a first task in it?" If the answer is no, stop. Do not make one on your own.

## New task (only when the user asks)
1. Which project? It must exist under `Projects/`. If it does not, offer to make it first.
2. Ask, one at a time: the **title** (3 to 8 words), the **goal** of the task (one line), and the **one next step** (can be left for later).
3. Run: `... task "<project>" "<title>" "<goal>" "<next step>"`
   It copies `Templates/STATUS.md`, sets it to `active`, adds an emoji to the title, tags it with the project's tag and fills the date. It refuses to overwrite an existing task.
4. Run `... currentwork` so Home shows it, then report the path in one line.

## Rules
- Never edit or delete an existing project or task with this skill.
- Never invent a goal, a next step or a PR number. Ask, or leave it for the user.
- Do not log to the daily note unless the user says "log this".
- If the script says `missing template` or `no such project`, say so and stop. Do not write the file by hand.
