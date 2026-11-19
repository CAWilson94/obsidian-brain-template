# Hooks and the file watcher (optional)

Run `./install.sh` first. It saves where `brain.py` lives, which the hooks read.

## Claude Code hooks
Add this to `~/.claude/settings.json` (merge it into any existing `hooks` block), with your own paths:
```json
{
  "hooks": {
    "SessionStart": [
      { "hooks": [ { "type": "command", "command": "/path/to/this-vault/hooks/task-status.sh" } ] }
    ],
    "Stop": [
      { "hooks": [ { "type": "command", "command": "python3 -I /path/to/this-vault/scripts/brain.py auto >/dev/null 2>&1 || true" } ] }
    ]
  }
}
```
- **SessionStart** lists your in-flight tasks when a session starts (needs `jq`).
- **Stop** runs `brain.py auto`: it logs `last_done` and `next` changes as `[auto]` lines in today's daily note and refreshes Home. It makes no model calls and never calls GitHub, so it is fast. Run `brain.py check` by hand for the GitHub part.

## File watcher (macOS)
It refreshes Home as soon as you save a note Home is built from: project pages, daily notes, side quests and 1-2-1s. It waits for macOS to report a change (no polling) and uses no model calls.
```bash
brew install fswatch
scripts/install_watch.sh          # turn off with: scripts/install_watch.sh --off
```
- It installs a login launch agent that runs a copy of `scripts/watch_projects.sh` from `~/.local/share/obsidian-brain/`, because macOS won't let launchd run scripts that sit in `~/Documents`.
- Logs: `~/Library/Logs/obsidian-brain-watch.log`.
- Re-run `install_watch.sh` after you change `watch_projects.sh`.

## Skills
`./install.sh` links every folder in `skills/` into `~/.claude/skills/`. It replaces an existing link with the same name, but skips a real folder. Start a new Claude Code session afterwards. The skills read `~/.config/obsidian-brain/` to find your brain.
