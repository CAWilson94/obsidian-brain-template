#!/bin/bash
# Keeps Home up to date: when a project note (Projects/<name>/*.md) is saved, run `brain.py currentwork`.
# Push based: fswatch sleeps until macOS reports a change (no polling, no model calls). Needs: brew install fswatch
SCRIPT="$(cat "$HOME/.config/obsidian-brain/script")"
ROOT="$(dirname "$SCRIPT")"
while [ "$ROOT" != "/" ] && [ ! -d "$ROOT/Projects" ]; do ROOT="$(dirname "$ROOT")"; done
[ -d "$ROOT/Projects" ] || { echo "no Projects folder found from $SCRIPT" >&2; exit 1; }
# fswatch prints one path per change. Act only on project notes (Projects/<name>/*.md); after one, swallow the rest of the burst
# (our own refresh may touch project notes, the next run then changes nothing).
/opt/homebrew/bin/fswatch -l 1 "$ROOT/Projects" |
  while read -r path; do
    [[ "$path" =~ /Projects/[^/]+/[^/]+\.md$ ]] || continue
    while read -r -t 2 _; do :; done
    /usr/local/bin/python3 -I "$SCRIPT" currentwork >/dev/null 2>&1
  done
