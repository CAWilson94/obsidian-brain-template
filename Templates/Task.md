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
> [!info] 🔗 Links, test instances, dashboards, diagrams for this task

## Initial Plan and Milestones
> [!note] 🪨 Where this came from (ticket link), risks, the plan, milestone dates
**Plan:**

**Questions (answered / new):**

## Points to Remember
> [!tip] 🔨 Quick notes on implementation: things to not forget
### Lifecycle and edge cases

### Failure and recovery

### Telemetry and debugging

## Live Notes
> [!success] 🎉 Doing it live! One heading per day, newest at the bottom

### <% tp.date.now("YYYY-MM-DD") %>

## Daily notes that mention this task
![[Daily For Task.base]]
