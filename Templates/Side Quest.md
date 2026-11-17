<%*
const title = await tp.system.prompt("Side quest title");
const emoji = (await tp.file.include("[[_emoji]]")).trim();
await tp.file.rename(`${emoji} ${title}`);
-%>
---
type: side-quest
status: Idea
tags: []
created: <% tp.date.now("YYYY-MM-DD") %>
why:
next:
---

## The idea
> [!tip] 🧭 Y'know, the shiny thing you spotted. What is it, and what made you notice it?

## Why it might be worth it
> [!note] 🎯 Who gets something out of this, and what gets easier

## First small step
> [!example] 🪜 The smallest thing that would tell you if it is worth more of your time
- [ ] 

## Notes
> [!quote] 💭 Just notes, links and dead ends, stream of consciousness
