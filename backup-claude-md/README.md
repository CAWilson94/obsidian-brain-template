# Backup of my global CLAUDE.md

A copy of `~/.claude/CLAUDE.md`: how I want Claude Code to work with me across every project (claims need `file:line`, one task active at a time, short replies, and so on).

## Restore on a new machine
```bash
# look first: this overwrites any CLAUDE.md you already have
ls -l ~/.claude/CLAUDE.md
cp backup-claude-md/CLAUDE.md ~/.claude/CLAUDE.md
```
Then fix the parts that name paths from the old machine (the vault location, `~/.claude/hooks/task-status.sh`, the cheat sheet).

## Update the backup
```bash
cp ~/.claude/CLAUDE.md backup-claude-md/CLAUDE.md
git add backup-claude-md && git commit -m "Refresh CLAUDE.md backup"
```

## Read this before you share the repo
This file contains **personal preferences**, including a note about how I like replies written, and paths from my own machine. The repo is private. **Delete this folder before making the repo public or sharing it as a template.**
Do not copy a project's checked-in `.claude/CLAUDE.md` (for example from a work repo) in here. Those belong to the project.
