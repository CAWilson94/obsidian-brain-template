<%*
const title = await tp.system.prompt("Epic title");
const emoji = (await tp.file.include("[[_emoji]]")).trim();
await tp.file.rename(`${emoji} ${title}`);
-%>
---
type: epic
status: Open
tags: []
created: <% tp.date.now("YYYY-MM-DD") %>
issue:
link:
---

## Goal
> [!note] 🎯 Y'know, what changes and for who

## Tasks in this epic
> [!info] 🧩 The tasks that make this up, link them here

## Decisions
