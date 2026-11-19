<%*
const emoji = (await tp.file.include("[[_emoji]]")).trim();
await tp.file.rename(`${emoji} Daily Dev Note ${tp.date.now("YYYY-MM-DD")}`);
-%>
---
type: daily
date: <% tp.date.now("YYYY-MM-DD") %>
tags: [<% tp.date.now("MMMM-YYYY").toLowerCase() %>-dev]
---

## Stand-up
> [!question] 🗣️ Stand-up stuff: what I did, what I'm up to, anything in the way

## Tasks I touched
> [!note] 🧩 Link the tasks from today, like [[Some Task]], and they show up on each task's page

## Links
> [!info] 🔗 Y'know, useful links from the day that you should go and put in a mega link page..

## Daily TODO:
> [!success] 🎁 The daily todo, what's happening right now.
- [ ] 

## Stream of Doing Notes
> [!quote] 💭 Just notes from the day, stream of consciousness to pick up things and have a searchable memory

**Open PRs:**

### <% tp.date.now("HH:mm") %>
