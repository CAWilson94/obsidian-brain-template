#!/usr/bin/env bash
# Links the skills in ./skills into ~/.claude/skills and tells the skills where this brain lives.
# Usage: ./install.sh            (installs for your user)
#        INSTALL_HOME=/tmp/x ./install.sh   (try it in a scratch home folder)
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
home="${INSTALL_HOME:-$HOME}"
script="${BRAIN_SCRIPT:-$here/scripts/brain.py}"
rules="${BRAIN_RULES:-$here/rules}"

[ -f "$script" ] || { echo "No brain.py at $script"; exit 1; }
mkdir -p "$home/.claude/skills" "$home/.config/obsidian-brain"
printf '%s\n' "$script" > "$home/.config/obsidian-brain/script"
printf '%s\n' "$rules" > "$home/.config/obsidian-brain/rules"
echo "brain.py -> $script"
echo "rules    -> $rules"

for dir in "$here"/skills/*/; do
  name="$(basename "$dir")"
  target="$home/.claude/skills/$name"
  if [ -e "$target" ] && [ ! -L "$target" ]; then
    echo "skipped $name: $target already exists and is not a link (move it away, then re-run)"
    continue
  fi
  ln -sfn "${dir%/}" "$target"
  echo "linked  $name"
done
echo "Done. Start a new Claude Code session so the skills load."
