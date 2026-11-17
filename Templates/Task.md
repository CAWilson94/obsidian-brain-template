<%*
const title = await tp.system.prompt("Task title");
const emoji = (await tp.file.include("[[_emoji]]")).trim();
await tp.file.rename(`${emoji} ${title}`);
-%>
---
type: task
status: To-do
tags: []
created: <% tp.date.now("YYYY-MM-DD") %>
ticket:
branch:
pr:
summary:
---

## Resources
> [!info] 🔗 Y'know, the links you keep needing: test instance, dashboards, Figma, that doc

## Initial Plan and Milestones
> [!note] 🪨 Where this came from (ticket link), the time-sink risks, the plan, and the milestone with a date
**Current plan:**

**Question I had (answered):**

**New question:**

## Points to Remember
> [!tip] 🔨 Some quick notes on implementation
### Lifecycle and edge cases

### Failure and recovery

### Telemetry and debugging

## Live Notes
> [!success] 🎉 Doing it live! One heading per day, newest at the bottom

### <% tp.date.now("YYYY-MM-DD") %>

## Daily notes that mention this task
![[Daily For Task.base]]
