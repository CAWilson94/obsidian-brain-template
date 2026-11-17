<%*
const emoji = (await tp.file.include("[[_emoji]]")).trim();
await tp.file.rename(`${emoji} Daily Dev Note ${tp.date.now("YYYY-MM-DD")}`);
-%>
---
type: daily
date: <% tp.date.now("YYYY-MM-DD") %>
tags: [<% tp.date.now("YYYY") %>]
---

## Stand-up
> [!question] 🗣️ What I did, what I'm doing, what's blocking me

## Tasks today
> [!note] 🔗 Link the tasks you touched, like [[Some Task]]. They show up on each task's page.

## Links
> [!info] 🔗 Useful links from the day, to move to a mega link page later

## Deadlines
> [!warning] ⏰ When things are due

## Rolling TODO
> [!example] 📌 Rolling todo: carried over or ongoing
- [ ] 

## Daily TODO
> [!success] 🎁 The daily todo: what's happening right now
- [ ] 

## Stream of Doing Notes
> [!quote] 💭 Stream of consciousness, so future-you has a searchable memory

**Open PRs:**

### <% tp.date.now("HH:mm") %>
