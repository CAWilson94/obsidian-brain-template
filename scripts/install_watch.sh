#!/bin/bash
# Installs (or with --off removes) a macOS launch agent that runs watch_projects.sh at login.
# Usage: scripts/install_watch.sh        scripts/install_watch.sh --off
set -euo pipefail
LABEL=com.obsidian-brain.watch
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
here="$(cd "$(dirname "$0")" && pwd)"
launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
if [ "${1:-}" = "--off" ]; then rm -f "$PLIST"; echo "watcher removed"; exit 0; fi
command -v fswatch >/dev/null || { echo "Install fswatch first: brew install fswatch"; exit 1; }
[ -f "$HOME/.config/obsidian-brain/script" ] || { echo "Run install.sh first (it saves the brain.py path)"; exit 1; }
# macOS will not let launchd run a script that sits in ~/Documents, so run a copy from ~/.local/share
run_dir="$HOME/.local/share/obsidian-brain"
mkdir -p "$HOME/Library/LaunchAgents" "$HOME/Library/Logs" "$run_dir"
cp "$here/watch_projects.sh" "$run_dir/watch_projects.sh"
chmod +x "$run_dir/watch_projects.sh"
cat > "$PLIST" <<PL
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key><array><string>/bin/bash</string><string>$run_dir/watch_projects.sh</string></array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardErrorPath</key><string>$HOME/Library/Logs/obsidian-brain-watch.log</string>
</dict></plist>
PL
launchctl bootstrap "gui/$(id -u)" "$PLIST"
echo "watcher running (turn off: $here/install_watch.sh --off)"
