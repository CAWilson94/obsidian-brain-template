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
> [!note] 🎯 What changes, for whom

## Tasks in this epic
> [!info] 🧩 Link each task note here

## Decisions
