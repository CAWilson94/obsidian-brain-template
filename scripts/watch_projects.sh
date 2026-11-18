#!/bin/bash
# Keeps Home up to date: when a project note (Projects/<name>/*.md) is saved, run `brain.py currentwork`.
# Push based: fswatch sleeps until macOS reports a change (no polling, no model calls). Needs: brew install fswatch
SCRIPT="$(cat "$HOME/.config/obsidian-brain/script")"
ROOT="$(dirname "$SCRIPT")"
while [ "$ROOT" != "/" ] && [ ! -d "$ROOT/Projects" ]; do ROOT="$(dirname "$ROOT")"; done
[ -d "$ROOT/Projects" ] || { echo "no Projects folder found from $SCRIPT" >&2; exit 1; }
# Watch project notes, daily notes, side quests and 1-2-1s: the notes Home's lists are built from.
BRAIN="$(dirname "$(dirname "$SCRIPT")")"
WATCH=("$ROOT/Projects")
for d in Daily SideQuests Meetings; do [ -d "$BRAIN/$d" ] && WATCH+=("$BRAIN/$d"); done
# fswatch prints one path per change. After a match, swallow the rest of the burst
# (our own refresh may touch notes, the next run then changes nothing).
/opt/homebrew/bin/fswatch -l 1 "${WATCH[@]}" |
  while read -r path; do
    [[ "$path" =~ /(Projects/[^/]+|Daily|SideQuests|Meetings)/[^/]+\.md$ ]] || continue
    while read -r -t 2 _; do :; done
    /usr/local/bin/python3 -I "$SCRIPT" currentwork >/dev/null 2>&1
  done
